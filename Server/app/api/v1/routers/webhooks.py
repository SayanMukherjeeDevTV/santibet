from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.api.v1.deps import get_db
from app.core.logging import get_logger
from app.models.wallet import OWNER_PAYMENT_CLEARING, PAYMENT_COMPLETED, PAYMENT_FAILED, Payment
from app.services import payment_service, wallet_service

router = APIRouter()
logger = get_logger(__name__)


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    session: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe-Signature header")

    stripe_provider = payment_service.get_stripe_provider()
    try:
        event = stripe_provider.verify_webhook(payload, stripe_signature)
    except payment_service.PaymentProviderError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        logger.warning("stripe_webhook_signature_invalid")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {})
    processor_ref = data_object.get("id")

    if event_type == "payment_intent.succeeded" and processor_ref:
        await _finalize_deposit(session, processor_ref, succeeded=True)
    elif event_type == "payment_intent.payment_failed" and processor_ref:
        await _finalize_deposit(session, processor_ref, succeeded=False)
    elif event_type == "payout.paid" and processor_ref:
        await _finalize_withdrawal(session, processor_ref, succeeded=True)
    elif event_type == "payout.failed" and processor_ref:
        await _finalize_withdrawal(session, processor_ref, succeeded=False)
    else:
        logger.info("stripe_webhook_ignored", event_type=event_type)

    return {"received": True}


async def _finalize_deposit(session: AsyncSession, processor_ref: str, *, succeeded: bool) -> None:
    payment = (
        await session.execute(select(Payment).where(Payment.processor_ref == processor_ref))
    ).scalar_one_or_none()
    if payment is None or payment.status == PAYMENT_COMPLETED:
        return  # unknown or already-finalized payment - idempotent no-op

    now = datetime.now(timezone.utc)
    if succeeded:
        payment.status = PAYMENT_COMPLETED
        payment.updated_at = now
        await wallet_service.credit_user(
            session, payment.user_id, Decimal(str(payment.amount)), reason="deposit",
            counter_owner_type=OWNER_PAYMENT_CLEARING, ref_type="payment", ref_id=payment.id,
        )
    else:
        payment.status = PAYMENT_FAILED
        payment.updated_at = now


async def _finalize_withdrawal(session: AsyncSession, processor_ref: str, *, succeeded: bool) -> None:
    """The withdrawal was already debited from the user (held) when it was
    requested (see wallet router). On success we just mark it completed; on
    failure we refund the held amount back to the user."""
    payment = (
        await session.execute(select(Payment).where(Payment.processor_ref == processor_ref))
    ).scalar_one_or_none()
    if payment is None or payment.status == PAYMENT_COMPLETED:
        return

    now = datetime.now(timezone.utc)
    if succeeded:
        payment.status = PAYMENT_COMPLETED
    else:
        payment.status = PAYMENT_FAILED
        await wallet_service.credit_user(
            session, payment.user_id, Decimal(str(payment.amount)), reason="refund",
            counter_owner_type=OWNER_PAYMENT_CLEARING, ref_type="payment", ref_id=payment.id,
        )
    payment.updated_at = now
