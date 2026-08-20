"""Market settlement: admin picks the winning outcome, every open position
on that outcome is paid out at $1.00/share from the platform treasury, and
every open position on a losing outcome is marked lost with no payout.

Idempotency: each position gets a unique payout_idempotency_key of
f"resolve:{market_id}:{position_id}" enforced by a UNIQUE constraint, so
re-running resolution for a market that partially failed (e.g. crashed
halfway through a huge trader base) never double-pays a position that
already got its payout - the second attempt just skips rows that already
have the key set.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import STATUS_RESOLVED, Market
from app.models.position import POSITION_LOST, POSITION_OPEN, POSITION_WON, Position
from app.models.wallet import OWNER_PLATFORM_TREASURY
from app.services import wallet_service


class MarketAlreadyResolvedError(Exception):
    pass


class InvalidOutcomeError(Exception):
    pass


async def resolve_market(
    session: AsyncSession, market: Market, winning_outcome_id: uuid.UUID, resolved_by: uuid.UUID
) -> dict:
    if market.status == STATUS_RESOLVED and market.payouts_processed_at is not None:
        raise MarketAlreadyResolvedError(f"Market {market.id} is already resolved and paid out")

    valid_outcome_ids = {o.id for o in market.outcomes}
    if winning_outcome_id not in valid_outcome_ids:
        raise InvalidOutcomeError(f"{winning_outcome_id} is not an outcome of market {market.id}")

    now = datetime.now(timezone.utc)
    market.status = STATUS_RESOLVED
    market.resolved_outcome_id = winning_outcome_id
    market.resolved_at = now

    stmt = select(Position).where(Position.market_id == market.id, Position.status == POSITION_OPEN)
    result = await session.execute(stmt)
    open_positions = list(result.scalars().all())

    winners_paid = 0
    losers_closed = 0
    total_paid_out = Decimal("0")

    for position in open_positions:
        idem_key = f"resolve:{market.id}:{position.id}"
        if position.outcome_id == winning_outcome_id:
            shares = Decimal(str(position.shares))
            payout = shares * Decimal("1.0000")
            await wallet_service.credit_user(
                session,
                position.user_id,
                payout,
                reason="payout",
                counter_owner_type=OWNER_PLATFORM_TREASURY,
                ref_type="position",
                ref_id=position.id,
            )
            position.status = POSITION_WON
            position.payout_idempotency_key = idem_key
            winners_paid += 1
            total_paid_out += payout
        else:
            position.status = POSITION_LOST
            position.payout_idempotency_key = idem_key
            losers_closed += 1
        position.closed_at = now

    market.payouts_processed_at = now
    await session.flush()

    return {
        "market_id": market.id,
        "winning_outcome_id": winning_outcome_id,
        "winners_paid": winners_paid,
        "losers_closed": losers_closed,
        "total_paid_out": total_paid_out,
        "resolved_by": resolved_by,
        "resolved_at": now,
    }
