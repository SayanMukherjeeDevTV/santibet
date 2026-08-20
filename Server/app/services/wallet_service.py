"""Double-entry ledger service.

Every balance-changing operation anywhere in the codebase MUST go through
`post_ledger_transaction`. No other code should INSERT into ledger_entries
directly, and nothing should ever UPDATE a "balance" column - there isn't
one. An account's balance is always SUM(credit) - SUM(debit) over its
ledger_entries rows.

This module also owns getting-or-creating the fixed platform accounts
(treasury, fees, payment clearing) and per-user accounts.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.models.wallet import (
    Account,
    DIRECTION_CREDIT,
    DIRECTION_DEBIT,
    LedgerEntry,
    OWNER_PAYMENT_CLEARING,
    OWNER_PLATFORM_FEES,
    OWNER_PLATFORM_TREASURY,
    OWNER_USER,
)


class InsufficientFundsError(Exception):
    pass


class LedgerImbalanceError(Exception):
    pass


@dataclass
class LedgerLeg:
    account_id: uuid.UUID
    direction: str  # "debit" | "credit"
    amount: Decimal
    owner_type: str = ""  # used only for the overdraft check, not persisted


def _balance_cache_key(account_id: uuid.UUID) -> str:
    return f"balance:{account_id}"


async def get_or_create_platform_account(
    session: AsyncSession, owner_type: str, currency: str = "USD"
) -> Account:
    stmt = select(Account).where(Account.owner_type == owner_type, Account.currency == currency)
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is None:
        account = Account(owner_type=owner_type, owner_id=None, currency=currency)
        session.add(account)
        await session.flush()
    return account


async def get_or_create_user_account(
    session: AsyncSession, user_id: uuid.UUID, currency: str = "USD"
) -> Account:
    stmt = select(Account).where(
        Account.owner_type == OWNER_USER, Account.owner_id == user_id, Account.currency == currency
    )
    result = await session.execute(stmt)
    account = result.scalar_one_or_none()
    if account is None:
        account = Account(owner_type=OWNER_USER, owner_id=user_id, currency=currency)
        session.add(account)
        await session.flush()
    return account


async def get_balance(session: AsyncSession, account_id: uuid.UUID, *, use_cache: bool = True) -> Decimal:
    redis = get_redis()
    cache_key = _balance_cache_key(account_id)
    if use_cache:
        cached = await redis.get(cache_key)
        if cached is not None:
            return Decimal(cached)

    stmt = select(
        LedgerEntry.direction, LedgerEntry.amount
    ).where(LedgerEntry.account_id == account_id)
    result = await session.execute(stmt)
    balance = Decimal("0")
    for direction, amount in result.all():
        amount = Decimal(str(amount))
        balance += amount if direction == DIRECTION_CREDIT else -amount

    await redis.set(cache_key, str(balance), ex=30)
    return balance


async def _invalidate_balance_cache(account_id: uuid.UUID) -> None:
    redis = get_redis()
    await redis.delete(_balance_cache_key(account_id))


async def post_ledger_transaction(
    session: AsyncSession,
    legs: list[LedgerLeg],
    *,
    reason: str,
    ref_type: str | None = None,
    ref_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Writes a balanced set of ledger legs atomically. Raises
    LedgerImbalanceError if debits != credits, and InsufficientFundsError if
    a `user` owner-type account would go negative. Platform accounts
    (treasury/fees/clearing) are allowed to go negative by design (e.g. the
    treasury subsidizes AMM liquidity and collects it back over time).

    Caller is expected to already be inside a transaction (the FastAPI `get_db`
    dependency wraps each request in one); this function does not commit.
    """
    if not legs:
        raise ValueError("post_ledger_transaction requires at least one leg")

    total_debit = sum((leg.amount for leg in legs if leg.direction == DIRECTION_DEBIT), Decimal("0"))
    total_credit = sum((leg.amount for leg in legs if leg.direction == DIRECTION_CREDIT), Decimal("0"))
    if total_debit != total_credit:
        raise LedgerImbalanceError(
            f"Ledger transaction does not balance: debit={total_debit} credit={total_credit}"
        )

    # Overdraft check for user cash accounts: simulate the effect of debit legs
    # against current balance before committing any of them.
    for leg in legs:
        if leg.direction == DIRECTION_DEBIT and leg.owner_type == OWNER_USER:
            current = await get_balance(session, leg.account_id, use_cache=False)
            if current - leg.amount < 0:
                raise InsufficientFundsError(
                    f"Account {leg.account_id} has insufficient funds for debit of {leg.amount}"
                )

    group_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    for leg in legs:
        session.add(
            LedgerEntry(
                transaction_group_id=group_id,
                account_id=leg.account_id,
                direction=leg.direction,
                amount=leg.amount,
                reason=reason,
                ref_type=ref_type,
                ref_id=ref_id,
                created_at=now,
            )
        )
    await session.flush()

    for leg in legs:
        await _invalidate_balance_cache(leg.account_id)

    return group_id


async def credit_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    amount: Decimal,
    *,
    reason: str,
    counter_owner_type: str = OWNER_PLATFORM_TREASURY,
    ref_type: str | None = None,
    ref_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Convenience helper: credit a user's cash account, debiting the given
    platform account for the other leg (deposits, payouts, refunds)."""
    user_account = await get_or_create_user_account(session, user_id)
    counter_account = await get_or_create_platform_account(session, counter_owner_type)
    legs = [
        LedgerLeg(account_id=counter_account.id, direction=DIRECTION_DEBIT, amount=amount, owner_type=counter_owner_type),
        LedgerLeg(account_id=user_account.id, direction=DIRECTION_CREDIT, amount=amount, owner_type=OWNER_USER),
    ]
    return await post_ledger_transaction(session, legs, reason=reason, ref_type=ref_type, ref_id=ref_id)


async def debit_user(
    session: AsyncSession,
    user_id: uuid.UUID,
    amount: Decimal,
    *,
    reason: str,
    counter_owner_type: str = OWNER_PLATFORM_TREASURY,
    ref_type: str | None = None,
    ref_id: uuid.UUID | None = None,
) -> uuid.UUID:
    """Convenience helper: debit a user's cash account (trades, withdrawals),
    crediting the given platform account for the other leg. Raises
    InsufficientFundsError if the user doesn't have enough balance."""
    user_account = await get_or_create_user_account(session, user_id)
    counter_account = await get_or_create_platform_account(session, counter_owner_type)
    legs = [
        LedgerLeg(account_id=user_account.id, direction=DIRECTION_DEBIT, amount=amount, owner_type=OWNER_USER),
        LedgerLeg(account_id=counter_account.id, direction=DIRECTION_CREDIT, amount=amount, owner_type=counter_owner_type),
    ]
    return await post_ledger_transaction(session, legs, reason=reason, ref_type=ref_type, ref_id=ref_id)
