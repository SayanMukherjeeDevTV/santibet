from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit
from app.models.market import Market as MarketModel
from app.models.trading import Trade
from app.models.user import KYC_APPROVED, KYC_PENDING, User
from app.models.wallet import (
    OWNER_PAYMENT_CLEARING,
    PAYMENT_COMPLETED,
    PAYMENT_HELD,
    PAYMENT_PENDING,
    Payment,
)
from app.schemas.wallet import (
    DepositRequest,
    DepositResponse,
    Transaction,
    WalletBalance,
    WithdrawRequest,
    WithdrawResponse,
)
from app.services import kyc_service, payment_service, wallet_service

router = APIRouter()
kyc_router = APIRouter()


@router.get("/balance", response_model=WalletBalance)
async def get_balance(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    account = await wallet_service.get_or_create_user_account(session, user.id)
    balance = await wallet_service.get_balance(session, account.id)

    pending_stmt = select(Payment).where(
        Payment.user_id == user.id, Payment.direction == "withdrawal", Payment.status == PAYMENT_HELD
    )
    pending = (await session.execute(pending_stmt)).scalars().all()
    pending_total = sum((Decimal(str(p.amount)) for p in pending), Decimal("0"))

    return WalletBalance(
        balance=float(balance),
        pending_withdrawals=float(pending_total),
        real_money_enabled=settings.platform_real_money_enabled,
    )


@router.get("/transactions", response_model=list[Transaction])
async def list_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Unions payments (deposits/withdrawals) and trades (buy/sell) into one
    reverse-chronological feed, matching the frontend's `Transaction` type."""
    account = await wallet_service.get_or_create_user_account(session, user.id)

    payments_stmt = (
        select(Payment).where(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(limit)
    )
    payments = (await session.execute(payments_stmt)).scalars().all()

    trades_stmt = (
        select(Trade, MarketModel)
        .join(MarketModel, MarketModel.id == Trade.market_id)
        .where((Trade.buyer_user_id == user.id) | (Trade.seller_user_id == user.id))
        .order_by(Trade.created_at.desc())
        .limit(limit)
    )
    trades = (await session.execute(trades_stmt)).all()

    running_balance = await wallet_service.get_balance(session, account.id)

    events: list[tuple[datetime, Transaction]] = []
    for p in payments:
        events.append(
            (
                p.created_at,
                Transaction(
                    id=p.id,
                    type=p.direction,
                    amount=float(p.amount),
                    balance_after=float(running_balance),  # approximate; see note below
                    status=p.status if p.status in ("completed", "pending", "failed") else "pending",
                    created_at=p.created_at,
                ),
            )
        )
    for t, market in trades:
        is_buyer = t.buyer_user_id == user.id
        notional = float(Decimal(str(t.price)) * Decimal(str(t.shares)))
        events.append(
            (
                t.created_at,
                Transaction(
                    id=t.id,
                    type="buy" if is_buyer else "sell",
                    market_id=market.id,
                    market_slug=market.slug,
                    question=market.question,
                    amount=-notional if is_buyer else notional,
                    balance_after=float(running_balance),
                    status="completed",
                    created_at=t.created_at,
                ),
            )
        )

    events.sort(key=lambda e: e[0], reverse=True)
    # NOTE: balance_after is reported as the current balance rather than a
    # true point-in-time running total, since ledger_entries doesn't store a
    # per-row running balance by design (see wallet_service docstring). A
    # future iteration could compute a true running total by replaying
    # ledger_entries for this account in chronological order if the exact
    # historical balance display becomes a product requirement.
    return [tx for _, tx in events[:limit]]


@router.post("/deposit", response_model=DepositResponse, status_code=status.HTTP_201_CREATED)
async def deposit(
    body: DepositRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await enforce_rate_limit(f"deposit:{user.id}", limit=10, window_seconds=3600)

    existing = (
        await session.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))
    ).scalar_one_or_none()
    if existing is not None:
        return DepositResponse(payment_id=existing.id, status=existing.status)

    now = datetime.now(timezone.utc)
    amount = Decimal(str(body.amount))

    if not settings.platform_real_money_enabled:
        # Demo/paper-money mode: credit the ledger directly, no processor.
        payment = Payment(
            id=uuid.uuid4(),
            user_id=user.id,
            direction="deposit",
            method="demo",
            processor="demo",
            processor_ref=None,
            amount=amount,
            status=PAYMENT_COMPLETED,
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
        )
        session.add(payment)
        await session.flush()
        await wallet_service.credit_user(
            session, user.id, amount, reason="deposit", counter_owner_type=OWNER_PAYMENT_CLEARING, ref_type="payment", ref_id=payment.id
        )
        return DepositResponse(payment_id=payment.id, status=PAYMENT_COMPLETED)

    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification required for real-money deposits")

    payment = Payment(
        id=uuid.uuid4(),
        user_id=user.id,
        direction="deposit",
        method=body.method,
        processor="stripe" if body.method in ("card", "bank") else "crypto",
        amount=amount,
        status=PAYMENT_PENDING,
        idempotency_key=idempotency_key,
        created_at=now,
        updated_at=now,
    )
    session.add(payment)
    await session.flush()

    if body.method in ("card", "bank"):
        stripe_provider = payment_service.get_stripe_provider()
        try:
            intent = await stripe_provider.create_deposit_intent(user_id=user.id, amount=amount)
        except payment_service.PaymentProviderError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
        payment.processor_ref = intent["processor_ref"]
        await session.flush()
        return DepositResponse(payment_id=payment.id, status=payment.status, client_secret=intent["client_secret"])
    else:
        crypto_provider = payment_service.get_crypto_provider()
        addr = await crypto_provider.create_deposit_address(user_id=user.id, currency="USDC")
        payment.processor_ref = addr["processor_ref"]
        await session.flush()
        return DepositResponse(
            payment_id=payment.id, status=payment.status, crypto_deposit_address=addr["address"], crypto_currency="USDC"
        )


@router.post("/withdraw", response_model=WithdrawResponse, status_code=status.HTTP_201_CREATED)
async def withdraw(
    body: WithdrawRequest,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await enforce_rate_limit(f"withdraw:{user.id}", limit=5, window_seconds=3600)

    existing = (
        await session.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))
    ).scalar_one_or_none()
    if existing is not None:
        return WithdrawResponse(payment_id=existing.id, status=existing.status)

    now = datetime.now(timezone.utc)
    amount = Decimal(str(body.amount))

    if not settings.platform_real_money_enabled:
        payment = Payment(
            id=uuid.uuid4(),
            user_id=user.id,
            direction="withdrawal",
            method="demo",
            processor="demo",
            amount=amount,
            status=PAYMENT_COMPLETED,
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
        )
        session.add(payment)
        await session.flush()
        await wallet_service.debit_user(
            session, user.id, amount, reason="withdrawal", counter_owner_type=OWNER_PAYMENT_CLEARING, ref_type="payment", ref_id=payment.id
        )
        return WithdrawResponse(payment_id=payment.id, status=PAYMENT_COMPLETED)

    if user.kyc_status != KYC_APPROVED or not user.is_real_money_eligible:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="KYC approval required for withdrawals")
    if user.region_code and user.region_code in settings.geofence_blocked_regions_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Withdrawals are not available in your region")

    # Move funds into a held state immediately (debit the user, credit
    # payment_clearing) so they can't be double-spent while the payout is
    # in flight; a Celery task reconciles this on processor success/failure.
    payment = Payment(
        id=uuid.uuid4(),
        user_id=user.id,
        direction="withdrawal",
        method=body.method,
        processor="stripe" if body.method == "bank" else "crypto",
        amount=amount,
        status=PAYMENT_HELD,
        idempotency_key=idempotency_key,
        created_at=now,
        updated_at=now,
    )
    session.add(payment)
    await session.flush()

    await wallet_service.debit_user(
        session, user.id, amount, reason="withdrawal", counter_owner_type=OWNER_PAYMENT_CLEARING, ref_type="payment", ref_id=payment.id
    )

    from app.workers.tasks import process_withdrawal_payout_task

    process_withdrawal_payout_task.delay(str(payment.id), body.destination)

    return WithdrawResponse(payment_id=payment.id, status=PAYMENT_HELD)


@kyc_router.get("/status")
async def kyc_status(user: User = Depends(get_current_user)):
    return {"status": user.kyc_status}


@kyc_router.post("/start", status_code=status.HTTP_201_CREATED)
async def kyc_start(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    provider = kyc_service.get_kyc_provider()
    session_info = await provider.start_verification(user_id=user.id)
    user.kyc_status = KYC_PENDING
    user.kyc_provider_ref = session_info["session_id"]
    await session.flush()
    return session_info
