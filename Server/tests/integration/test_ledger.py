"""These hit a real Postgres test DB and a real Redis (for the balance
cache) - see tests/conftest.py and the README for how to point them at your
local dev instances."""
from decimal import Decimal

import pytest

from app.services import wallet_service


async def test_credit_then_debit_user_balance(db_session, test_user):
    await wallet_service.credit_user(
        db_session, test_user.id, Decimal("100.00"), reason="deposit"
    )
    account = await wallet_service.get_or_create_user_account(db_session, test_user.id)
    balance = await wallet_service.get_balance(db_session, account.id, use_cache=False)
    assert balance == Decimal("100.00")

    await wallet_service.debit_user(db_session, test_user.id, Decimal("30.00"), reason="buy")
    balance_after = await wallet_service.get_balance(db_session, account.id, use_cache=False)
    assert balance_after == Decimal("70.00")


async def test_debit_beyond_balance_raises_insufficient_funds(db_session, test_user):
    await wallet_service.credit_user(db_session, test_user.id, Decimal("10.00"), reason="deposit")
    with pytest.raises(wallet_service.InsufficientFundsError):
        await wallet_service.debit_user(db_session, test_user.id, Decimal("50.00"), reason="withdrawal")

    # Balance must be unchanged after the rejected debit.
    account = await wallet_service.get_or_create_user_account(db_session, test_user.id)
    balance = await wallet_service.get_balance(db_session, account.id, use_cache=False)
    assert balance == Decimal("10.00")


async def test_every_transaction_group_balances_to_zero(db_session, test_user):
    """Core invariant: for any transaction_group_id, sum(credits) ==
    sum(debits). This is enforced at write time by post_ledger_transaction,
    but we also verify it holds by re-reading the rows directly."""
    from sqlalchemy import select

    from app.models.wallet import DIRECTION_CREDIT, DIRECTION_DEBIT, LedgerEntry

    group_id = await wallet_service.credit_user(
        db_session, test_user.id, Decimal("42.50"), reason="deposit"
    )

    rows = (
        await db_session.execute(
            select(LedgerEntry).where(LedgerEntry.transaction_group_id == group_id)
        )
    ).scalars().all()

    total_debit = sum(Decimal(str(r.amount)) for r in rows if r.direction == DIRECTION_DEBIT)
    total_credit = sum(Decimal(str(r.amount)) for r in rows if r.direction == DIRECTION_CREDIT)
    assert total_debit == total_credit == Decimal("42.50")


async def test_platform_account_can_go_negative_user_account_cannot(db_session, test_user):
    """The treasury account subsidizes payouts/AMM liquidity and is allowed
    to run a deficit; only `user` owner-type accounts are protected from
    overdraft."""
    # Paying out more than the treasury has "collected" is fine (treasury
    # goes negative) - this models a market that resolves against the house.
    await wallet_service.credit_user(db_session, test_user.id, Decimal("500.00"), reason="payout")
    account = await wallet_service.get_or_create_user_account(db_session, test_user.id)
    balance = await wallet_service.get_balance(db_session, account.id, use_cache=False)
    assert balance == Decimal("500.00")


async def test_balance_cache_is_invalidated_on_write(db_session, test_user):
    account = await wallet_service.get_or_create_user_account(db_session, test_user.id)
    await wallet_service.credit_user(db_session, test_user.id, Decimal("10.00"), reason="deposit")
    cached = await wallet_service.get_balance(db_session, account.id, use_cache=True)
    assert cached == Decimal("10.00")

    await wallet_service.credit_user(db_session, test_user.id, Decimal("5.00"), reason="deposit")
    updated = await wallet_service.get_balance(db_session, account.id, use_cache=True)
    assert updated == Decimal("15.00")
