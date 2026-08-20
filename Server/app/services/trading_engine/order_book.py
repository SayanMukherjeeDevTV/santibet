"""Central limit order book half of the hybrid engine: reconstructing
bid/ask levels for display, and matching an incoming taker against resting
maker orders using price-time priority.

Resting orders live in the `orders` table (status in open/partially_filled).
No separate in-memory book is kept - Postgres is the source of truth. For
the trading volumes this project is designed for, querying+locking the
handful of relevant rows per match is simple and correct; a future
high-frequency version could move this into an in-memory structure fed by
the same table via logical replication.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trading import (
    ORDER_FILLED,
    ORDER_OPEN,
    ORDER_PARTIALLY_FILLED,
    Order,
    SIDE_BUY,
    SIDE_SELL,
)


@dataclass
class BookLevel:
    price: Decimal
    size: Decimal


@dataclass
class MakerFill:
    maker_order: Order
    price: Decimal
    shares: Decimal


async def get_resting_orders(
    session: AsyncSession, market_id: uuid.UUID, outcome_id: uuid.UUID, side: str
) -> list[Order]:
    """Resting orders for one side, best price first then oldest first
    (price-time priority). Locked FOR UPDATE so concurrent matches against
    the same orders can't double-fill them."""
    stmt = (
        select(Order)
        .where(
            Order.market_id == market_id,
            Order.outcome_id == outcome_id,
            Order.side == side,
            Order.status.in_([ORDER_OPEN, ORDER_PARTIALLY_FILLED]),
            Order.order_type == "limit",
        )
        .order_by(
            Order.limit_price.desc() if side == SIDE_BUY else Order.limit_price.asc(),
            Order.created_at.asc(),
        )
        .with_for_update()
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def build_book_levels(orders: list[Order]) -> list[BookLevel]:
    """Aggregate individual resting orders into price levels with
    cumulative running size, matching OrderBookEntry semantics
    ({price, size, total})."""
    levels: dict[Decimal, Decimal] = {}
    for order in orders:
        remaining = Decimal(str(order.shares_requested)) - Decimal(str(order.shares_filled))
        if remaining <= 0:
            continue
        price = Decimal(str(order.limit_price))
        levels[price] = levels.get(price, Decimal("0")) + remaining
    return [BookLevel(price=p, size=s) for p, s in sorted(levels.items())]


async def match_against_book(
    session: AsyncSession,
    market_id: uuid.UUID,
    outcome_id: uuid.UUID,
    taker_side: str,
    shares_wanted: Decimal,
    limit_price: Decimal | None,
) -> tuple[list[MakerFill], Decimal]:
    """Walk resting opposite-side orders in price-time priority, filling up
    to `shares_wanted`. A `limit_price` bounds how far the taker is willing
    to cross (None = market order, cross at any price). Mutates maker Order
    rows in place (shares_filled, status) but does not flush/commit - caller
    controls the transaction. Returns (fills, shares_still_unfilled).
    """
    opposite_side = SIDE_SELL if taker_side == SIDE_BUY else SIDE_BUY
    resting = await get_resting_orders(session, market_id, outcome_id, opposite_side)

    fills: list[MakerFill] = []
    remaining = shares_wanted

    for maker in resting:
        if remaining <= 0:
            break

        maker_price = Decimal(str(maker.limit_price))
        if limit_price is not None:
            crosses = maker_price <= limit_price if taker_side == SIDE_BUY else maker_price >= limit_price
            if not crosses:
                break

        maker_remaining = Decimal(str(maker.shares_requested)) - Decimal(str(maker.shares_filled))
        if maker_remaining <= 0:
            continue

        fill_shares = min(maker_remaining, remaining)
        maker.shares_filled = Decimal(str(maker.shares_filled)) + fill_shares
        maker.status = (
            ORDER_FILLED
            if Decimal(str(maker.shares_filled)) >= Decimal(str(maker.shares_requested))
            else ORDER_PARTIALLY_FILLED
        )

        fills.append(MakerFill(maker_order=maker, price=maker_price, shares=fill_shares))
        remaining -= fill_shares

    return fills, remaining
