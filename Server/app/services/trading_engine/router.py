"""Order routing: given an incoming taker order, decide how much fills
against resting limit orders (better prices, no AMM slippage) versus the
LMSR AMM pool (always-available but with price impact).

This is the backend for the frontend's "Smart Order Routing" panel, which
today shows a hardcoded Polymarket/Kalshi split. There is no external
exchange integration in this version - the two real liquidity sources are
our own order book and our own AMM pool, so the FillPlan below reports the
split between "order_book" and "amm" instead.

Strategy per order type:
  - market / IOC: sweep the book first (price-time priority, unbounded by
    limit_price), then send any remainder to the AMM. Market orders always
    fully fill (AMM has notional infinite depth, bounded only by price
    impact) unless FOK and the book+AMM together can't reasonably fill.
  - limit, GTC: match against the book AND the AMM wherever their price is
    at or better than the limit; whatever's left over rests on the book as
    a new order (handled by the caller, not this module).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trading import AMMPool, SIDE_BUY
from app.services.trading_engine import amm
from app.services.trading_engine.order_book import MakerFill, match_against_book


@dataclass
class RouteLeg:
    source: str  # "order_book" | "amm"
    price: Decimal
    shares: Decimal
    maker_order_id: uuid.UUID | None = None


@dataclass
class FillPlan:
    legs: list[RouteLeg] = field(default_factory=list)
    shares_filled: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")  # signed: positive = taker pays, negative = taker receives
    shares_unfilled: Decimal = Decimal("0")

    @property
    def avg_price(self) -> Decimal:
        if self.shares_filled == 0:
            return Decimal("0")
        return abs(self.total_cost) / self.shares_filled


def load_pool_quantities(pool: AMMPool) -> dict[str, Decimal]:
    return {k: Decimal(v) for k, v in pool.outcome_shares.items()}


def save_pool_quantities(pool: AMMPool, q: dict[str, Decimal]) -> None:
    pool.outcome_shares = {k: str(v) for k, v in q.items()}
    pool.updated_at = datetime.now(timezone.utc)


async def route_by_shares(
    session: AsyncSession,
    *,
    market_id: uuid.UUID,
    outcome_id: uuid.UUID,
    pool: AMMPool,
    side: str,
    shares_wanted: Decimal,
    limit_price: Decimal | None,
    allow_amm: bool,
) -> FillPlan:
    plan = FillPlan()

    book_fills, remaining = await match_against_book(
        session, market_id, outcome_id, side, shares_wanted, limit_price
    )
    for f in book_fills:
        signed_cost = f.price * f.shares if side == SIDE_BUY else -(f.price * f.shares)
        plan.legs.append(
            RouteLeg(source="order_book", price=f.price, shares=f.shares, maker_order_id=f.maker_order.id)
        )
        plan.shares_filled += f.shares
        plan.total_cost += signed_cost

    if remaining > 0 and allow_amm:
        b = Decimal(str(pool.liquidity_param))
        q = load_pool_quantities(pool)
        delta = remaining if side == SIDE_BUY else -remaining

        # If a limit price is set, cap how far the AMM fill is allowed to move
        # the price: only fill the portion of `remaining` whose marginal AMM
        # price stays within the limit. We approximate by checking the
        # instantaneous price before committing the full remaining size, and
        # otherwise fill nothing further via AMM (the order just rests, or -
        # for a market order there is no limit_price to violate).
        if limit_price is not None:
            current_prices = amm.prices(q, b)
            current_price = current_prices.get(str(outcome_id), Decimal("0.5"))
            crosses = current_price <= limit_price if side == SIDE_BUY else current_price >= limit_price
            if not crosses:
                remaining = Decimal("0")

        if remaining > 0:
            cost = amm.cost_to_trade(q, b, str(outcome_id), delta)
            q[str(outcome_id)] = q.get(str(outcome_id), Decimal("0")) + delta
            save_pool_quantities(pool, q)

            plan.legs.append(RouteLeg(source="amm", price=amm.avg_price(cost, remaining), shares=remaining))
            plan.shares_filled += remaining
            plan.total_cost += cost  # already signed correctly by amm.cost_to_trade (buy=+, sell=-)
            remaining = Decimal("0")

    plan.shares_unfilled = remaining
    return plan


async def route_by_amount(
    session: AsyncSession,
    *,
    market_id: uuid.UUID,
    outcome_id: uuid.UUID,
    pool: AMMPool,
    side: str,
    amount_wanted: Decimal,
) -> FillPlan:
    """Only used for market BUY orders sized in dollars rather than shares
    (the trade panel's "amount" mode). Walks the book level by level
    spending the dollar budget, then spends whatever's left on the AMM."""
    plan = FillPlan()
    budget = amount_wanted

    # Walk book one resting order at a time (already price-time sorted by
    # match_against_book's underlying query), spending `budget` as we go.
    # We do this by repeatedly asking match_against_book for a small share
    # slice is inefficient; instead fetch resting orders directly here.
    from app.services.trading_engine.order_book import get_resting_orders
    from app.models.trading import SIDE_SELL, ORDER_FILLED, ORDER_PARTIALLY_FILLED

    opposite_side = SIDE_SELL if side == SIDE_BUY else SIDE_BUY
    resting = await get_resting_orders(session, market_id, outcome_id, opposite_side)

    for maker in resting:
        if budget <= 0:
            break
        maker_price = Decimal(str(maker.limit_price))
        maker_remaining = Decimal(str(maker.shares_requested)) - Decimal(str(maker.shares_filled))
        if maker_remaining <= 0:
            continue

        max_affordable_shares = budget / maker_price
        fill_shares = min(maker_remaining, max_affordable_shares)
        if fill_shares <= 0:
            break

        fill_cost = fill_shares * maker_price
        maker.shares_filled = Decimal(str(maker.shares_filled)) + fill_shares
        maker.status = (
            ORDER_FILLED
            if Decimal(str(maker.shares_filled)) >= Decimal(str(maker.shares_requested))
            else ORDER_PARTIALLY_FILLED
        )

        plan.legs.append(
            RouteLeg(source="order_book", price=maker_price, shares=fill_shares, maker_order_id=maker.id)
        )
        plan.shares_filled += fill_shares
        plan.total_cost += fill_cost
        budget -= fill_cost

    if budget > 0:
        b = Decimal(str(pool.liquidity_param))
        q = load_pool_quantities(pool)
        amm_shares = amm.shares_for_amount(q, b, str(outcome_id), budget, is_buy=(side == SIDE_BUY))
        if amm_shares > 0:
            delta = amm_shares if side == SIDE_BUY else -amm_shares
            cost = amm.cost_to_trade(q, b, str(outcome_id), delta)
            q[str(outcome_id)] = q.get(str(outcome_id), Decimal("0")) + delta
            save_pool_quantities(pool, q)

            plan.legs.append(RouteLeg(source="amm", price=amm.avg_price(cost, amm_shares), shares=amm_shares))
            plan.shares_filled += amm_shares
            plan.total_cost += cost
            budget -= abs(cost)

    plan.shares_unfilled = Decimal("0")  # amount-denominated market orders are always "fully spent"
    return plan
