"""Applies a shares delta to a user's position in a market outcome, handling
weighted-average cost basis on the way in and proportional cost reduction on
the way out. Used by trade execution (both taker and maker legs).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.position import POSITION_OPEN, POSITION_SOLD, Position


class InsufficientSharesError(Exception):
    pass


async def get_open_position(
    session: AsyncSession, user_id: uuid.UUID, market_id: uuid.UUID, outcome_id: uuid.UUID
) -> Position | None:
    stmt = select(Position).where(
        Position.user_id == user_id,
        Position.market_id == market_id,
        Position.outcome_id == outcome_id,
        Position.status == POSITION_OPEN,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def apply_position_delta(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    market_id: uuid.UUID,
    outcome_id: uuid.UUID,
    shares_delta: Decimal,
    price: Decimal,
    now: datetime,
) -> Position:
    """shares_delta > 0 = acquiring shares (buy), < 0 = disposing shares (sell).
    Raises InsufficientSharesError if a sell would take shares negative."""
    position = await get_open_position(session, user_id, market_id, outcome_id)

    if shares_delta > 0:
        if position is None:
            position = Position(
                id=uuid.uuid4(),
                user_id=user_id,
                market_id=market_id,
                outcome_id=outcome_id,
                shares=shares_delta,
                avg_price=price,
                invested=price * shares_delta,
                status=POSITION_OPEN,
                opened_at=now,
            )
            session.add(position)
        else:
            old_shares = Decimal(str(position.shares))
            old_invested = Decimal(str(position.invested))
            new_shares = old_shares + shares_delta
            new_invested = old_invested + price * shares_delta
            position.shares = new_shares
            position.invested = new_invested
            position.avg_price = (new_invested / new_shares) if new_shares > 0 else Decimal("0")
    else:
        dispose = -shares_delta
        if position is None or Decimal(str(position.shares)) < dispose:
            raise InsufficientSharesError(
                f"User {user_id} does not have {dispose} shares of outcome {outcome_id} to sell"
            )
        old_shares = Decimal(str(position.shares))
        old_invested = Decimal(str(position.invested))
        remaining_shares = old_shares - dispose
        # Reduce invested proportionally so avg_price is preserved for the
        # remaining shares (standard weighted-average-cost accounting).
        proportion_remaining = (remaining_shares / old_shares) if old_shares > 0 else Decimal("0")
        position.shares = remaining_shares
        position.invested = old_invested * proportion_remaining
        if remaining_shares <= 0:
            position.status = POSITION_SOLD
            position.closed_at = now

    await session.flush()
    return position
