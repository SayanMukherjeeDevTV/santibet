"""Orchestrates placing an order end-to-end: validates the request, routes
the fill across the order book and AMM (app.services.trading_engine), posts
every resulting cash movement through the ledger in one atomic transaction,
updates positions for the taker and every filled maker, records price
history, refreshes market stats, and publishes a realtime event. The router
module (app/api/v1/routers/trading.py) stays a thin HTTP adapter over this.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis, market_channel, user_channel
from app.models.market import Market, MarketOutcome, MarketStats, PriceHistory, STATUS_ACTIVE
from app.models.trading import (
    AMMPool,
    ORDER_CANCELLED,
    ORDER_FILLED,
    ORDER_OPEN,
    ORDER_PARTIALLY_FILLED,
    Order,
    SIDE_BUY,
    SIDE_SELL,
    Trade,
)
from app.models.wallet import OWNER_PLATFORM_FEES, OWNER_PLATFORM_TREASURY, OWNER_USER
from app.services import position_service, wallet_service
from app.services.trading_engine import amm as amm_math
from app.services.trading_engine.router import FillPlan, route_by_amount, route_by_shares


class MarketNotTradableError(Exception):
    pass


class InvalidOrderError(Exception):
    pass


class FillOrKillError(Exception):
    pass


async def _get_amm_pool_locked(session: AsyncSession, market_id: uuid.UUID) -> AMMPool:
    stmt = select(AMMPool).where(AMMPool.market_id == market_id).with_for_update()
    pool = (await session.execute(stmt)).scalar_one_or_none()
    if pool is None:
        raise MarketNotTradableError(f"Market {market_id} has no AMM pool configured")
    return pool


async def _record_price_history(session: AsyncSession, market_id: uuid.UUID, pool: AMMPool, now: datetime) -> None:
    """Every fill moves the LMSR price of *every* outcome (they're
    complementary), so we snapshot all of them together at the same
    timestamp - this is what lets the frontend's combined {t, yes, no}
    series line up cleanly."""
    from app.services.trading_engine.router import load_pool_quantities

    q = load_pool_quantities(pool)
    b = Decimal(str(pool.liquidity_param))
    current_prices = amm_math.prices(q, b)

    outcomes = (
        await session.execute(select(MarketOutcome).where(MarketOutcome.market_id == market_id))
    ).scalars().all()
    for o in outcomes:
        price = current_prices.get(str(o.id))
        if price is None:
            continue
        session.add(PriceHistory(market_id=market_id, outcome_id=o.id, price=price, ts=now))
    await session.flush()


async def _refresh_market_stats_incremental(
    session: AsyncSession, market_id: uuid.UUID, trade_notional: Decimal, now: datetime
) -> None:
    stats = await session.get(MarketStats, market_id)
    if stats is None:
        stats = MarketStats(
            market_id=market_id, liquidity=0, total_volume=0, volume_24h=0, trader_count=0, updated_at=now
        )
        session.add(stats)
    stats.total_volume = Decimal(str(stats.total_volume)) + trade_notional
    stats.volume_24h = Decimal(str(stats.volume_24h)) + trade_notional  # coarse; refined by the periodic job
    stats.updated_at = now
    await session.flush()


async def _publish_market_event(market_slug: str, payload: dict) -> None:
    try:
        redis = get_redis()
        await redis.publish(market_channel(market_slug), json.dumps(payload, default=str))
    except Exception:
        pass  # realtime is best-effort; never fail the trade because pubsub is down


async def _publish_user_event(user_id: uuid.UUID, payload: dict) -> None:
    try:
        redis = get_redis()
        await redis.publish(user_channel(str(user_id)), json.dumps(payload, default=str))
    except Exception:
        pass


async def _reserved_buy_notional(
    session: AsyncSession, user_id: uuid.UUID, exclude_order_id: uuid.UUID | None = None
) -> Decimal:
    """Total dollar notional already committed to this user's other resting
    BUY limit orders (across all markets, since cash is fungible platform-wide)."""
    stmt = select(Order).where(
        Order.user_id == user_id,
        Order.side == SIDE_BUY,
        Order.order_type == "limit",
        Order.status.in_([ORDER_OPEN, ORDER_PARTIALLY_FILLED]),
    )
    orders = (await session.execute(stmt)).scalars().all()
    total = Decimal("0")
    for o in orders:
        if exclude_order_id is not None and o.id == exclude_order_id:
            continue
        remaining = Decimal(str(o.shares_requested)) - Decimal(str(o.shares_filled))
        total += remaining * Decimal(str(o.limit_price))
    return total


async def _reserved_sell_shares(
    session: AsyncSession,
    user_id: uuid.UUID,
    market_id: uuid.UUID,
    outcome_id: uuid.UUID,
    exclude_order_id: uuid.UUID | None = None,
) -> Decimal:
    """Shares already committed to this user's other resting SELL orders on
    this exact market+outcome."""
    stmt = select(Order).where(
        Order.user_id == user_id,
        Order.market_id == market_id,
        Order.outcome_id == outcome_id,
        Order.side == SIDE_SELL,
        Order.status.in_([ORDER_OPEN, ORDER_PARTIALLY_FILLED]),
    )
    orders = (await session.execute(stmt)).scalars().all()
    total = Decimal("0")
    for o in orders:
        if exclude_order_id is not None and o.id == exclude_order_id:
            continue
        total += Decimal(str(o.shares_requested)) - Decimal(str(o.shares_filled))
    return total


async def place_order(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    market: Market,
    outcome_id: uuid.UUID,
    side: str,
    order_type: str,
    time_in_force: str,
    shares: Decimal | None,
    amount: Decimal | None,
    limit_price: Decimal | None,
    idempotency_key: str | None,
) -> Order:
    if market.status != STATUS_ACTIVE:
        raise MarketNotTradableError(f"Market {market.slug} is not open for trading")

    if idempotency_key:
        existing = (
            await session.execute(select(Order).where(Order.idempotency_key == idempotency_key))
        ).scalar_one_or_none()
        if existing is not None:
            return existing

    if order_type == "limit" and limit_price is None:
        raise InvalidOrderError("limit_price is required for limit orders")
    if side == "sell" and shares is None:
        raise InvalidOrderError("shares is required for sell orders")
    if amount is not None and shares is not None:
        raise InvalidOrderError("Specify either shares or amount, not both")
    if amount is None and shares is None:
        raise InvalidOrderError("Either shares or amount is required")

    now = datetime.now(timezone.utc)

    if side == "sell":
        position = await position_service.get_open_position(session, user_id, market.id, outcome_id)
        owned = Decimal(str(position.shares)) if position else Decimal("0")
        reserved = await _reserved_sell_shares(session, user_id, market.id, outcome_id)
        available = owned - reserved
        if shares is not None and shares > available:
            raise InvalidOrderError(
                f"Insufficient available shares: own {owned}, {reserved} already committed to other "
                f"open sell orders, {available} available, requested {shares}"
            )

    if side == "buy" and order_type == "limit" and limit_price is not None:
        required_cash = amount if amount is not None else (shares * limit_price if shares is not None else Decimal("0"))
        balance = await wallet_service.get_balance(
            session, (await wallet_service.get_or_create_user_account(session, user_id)).id, use_cache=False
        )
        reserved_notional = await _reserved_buy_notional(session, user_id)
        available_cash = balance - reserved_notional
        if required_cash > available_cash:
            raise InvalidOrderError(
                f"Insufficient available buying power: balance {balance}, {reserved_notional} already "
                f"committed to other open buy orders, {available_cash} available, order requires {required_cash}"
            )

    order = Order(
        id=uuid.uuid4(),
        user_id=user_id,
        market_id=market.id,
        outcome_id=outcome_id,
        side=side,
        order_type=order_type,
        time_in_force=time_in_force,
        limit_price=limit_price,
        shares_requested=shares if shares is not None else Decimal("0"),
        shares_filled=Decimal("0"),
        status=ORDER_OPEN,
        idempotency_key=idempotency_key,
    )
    session.add(order)
    await session.flush()

    pool = await _get_amm_pool_locked(session, market.id)
    allow_amm = order_type == "market" or limit_price is not None

    if amount is not None:
        plan = await route_by_amount(
            session, market_id=market.id, outcome_id=outcome_id, pool=pool, side=side, amount_wanted=amount
        )
    else:
        plan = await route_by_shares(
            session,
            market_id=market.id,
            outcome_id=outcome_id,
            pool=pool,
            side=side,
            shares_wanted=shares,
            limit_price=limit_price,
            allow_amm=allow_amm,
        )

    if time_in_force == "FOK" and plan.shares_unfilled > 0:
        raise FillOrKillError("Order could not be fully filled")

    if plan.shares_filled > 0:
        await _settle_fill_plan(session, order=order, market=market, outcome_id=outcome_id, side=side, plan=plan, now=now)

    order.shares_filled = plan.shares_filled
    if order.order_type == "market" and shares is not None:
        order.shares_requested = plan.shares_filled  # market orders are "requested = filled" by definition

    if plan.shares_unfilled == 0:
        order.status = ORDER_FILLED
    elif plan.shares_filled > 0:
        order.status = ORDER_PARTIALLY_FILLED
    else:
        order.status = ORDER_OPEN

    # GTC limit orders with leftover simply stay open/partially_filled and
    # rest on the book (already persisted as an Order row; match_against_book
    # will find them on the next incoming taker). IOC never rests - cancel
    # whatever didn't fill immediately.
    if order.time_in_force == "IOC" and plan.shares_unfilled > 0 and order.status != ORDER_FILLED:
        order.status = ORDER_CANCELLED if plan.shares_filled == 0 else ORDER_PARTIALLY_FILLED

    await session.flush()

    await _record_price_history(session, market.id, pool, now)
    if plan.total_cost != 0:
        await _refresh_market_stats_incremental(session, market.id, abs(plan.total_cost), now)

    await _publish_market_event(
        market.slug,
        {
            "type": "trade",
            "outcomeId": str(outcome_id),
            "side": side,
            "shares": str(plan.shares_filled),
            "avgPrice": str(plan.avg_price),
        },
    )
    await _publish_user_event(user_id, {"type": "order_update", "orderId": str(order.id), "status": order.status})

    return order


async def _settle_fill_plan(
    session: AsyncSession,
    *,
    order: Order,
    market: Market,
    outcome_id: uuid.UUID,
    side: str,
    plan: FillPlan,
    now: datetime,
) -> None:
    legs: list[wallet_service.LedgerLeg] = []
    taker_account = await wallet_service.get_or_create_user_account(session, order.user_id)
    treasury_account = await wallet_service.get_or_create_platform_account(session, OWNER_PLATFORM_TREASURY)
    fees_account = await wallet_service.get_or_create_platform_account(session, OWNER_PLATFORM_FEES)

    gross_notional = Decimal("0")

    for leg in plan.legs:
        notional = leg.price * leg.shares
        gross_notional += notional

        maker_order = None
        if leg.source == "amm":
            counter_account = treasury_account
            counter_owner = OWNER_PLATFORM_TREASURY
        else:
            maker_order = await session.get(Order, leg.maker_order_id)
            counter_account = await wallet_service.get_or_create_user_account(session, maker_order.user_id)
            counter_owner = OWNER_USER
            # Maker's position moves opposite to the taker's.
            maker_delta = -leg.shares if side == SIDE_BUY else leg.shares
            await position_service.apply_position_delta(
                session,
                user_id=maker_order.user_id,
                market_id=market.id,
                outcome_id=outcome_id,
                shares_delta=maker_delta,
                price=leg.price,
                now=now,
            )
            await _publish_user_event(
                maker_order.user_id,
                {"type": "order_update", "orderId": str(maker_order.id), "status": maker_order.status},
            )

        if side == SIDE_BUY:
            legs.append(
                wallet_service.LedgerLeg(account_id=taker_account.id, direction="debit", amount=notional, owner_type=OWNER_USER)
            )
            legs.append(
                wallet_service.LedgerLeg(account_id=counter_account.id, direction="credit", amount=notional, owner_type=counter_owner)
            )
        else:
            legs.append(
                wallet_service.LedgerLeg(account_id=counter_account.id, direction="debit", amount=notional, owner_type=counter_owner)
            )
            legs.append(
                wallet_service.LedgerLeg(account_id=taker_account.id, direction="credit", amount=notional, owner_type=OWNER_USER)
            )

        session.add(
            Trade(
                id=uuid.uuid4(),
                market_id=market.id,
                outcome_id=outcome_id,
                taker_order_id=order.id,
                maker_order_id=leg.maker_order_id,
                fill_source=leg.source,
                price=leg.price,
                shares=leg.shares,
                taker_side=side,
                buyer_user_id=order.user_id if side == SIDE_BUY else (maker_order.user_id if maker_order else None),
                seller_user_id=order.user_id if side == SIDE_SELL else (maker_order.user_id if maker_order else None),
                fee=Decimal("0"),
                created_at=now,
            )
        )

    fee = (gross_notional * Decimal(settings.taker_fee_bps) / Decimal(10000)).quantize(Decimal("0.0001"))
    if fee > 0:
        legs.append(wallet_service.LedgerLeg(account_id=taker_account.id, direction="debit", amount=fee, owner_type=OWNER_USER))
        legs.append(wallet_service.LedgerLeg(account_id=fees_account.id, direction="credit", amount=fee, owner_type=OWNER_PLATFORM_FEES))

    await wallet_service.post_ledger_transaction(session, legs, reason=side, ref_type="order", ref_id=order.id)

    taker_delta = plan.shares_filled if side == SIDE_BUY else -plan.shares_filled
    await position_service.apply_position_delta(
        session,
        user_id=order.user_id,
        market_id=market.id,
        outcome_id=outcome_id,
        shares_delta=taker_delta,
        price=plan.avg_price,
        now=now,
    )


async def cancel_order(session: AsyncSession, user_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    order = await session.get(Order, order_id)
    if order is None or order.user_id != user_id:
        raise InvalidOrderError("Order not found")
    if order.status not in (ORDER_OPEN, ORDER_PARTIALLY_FILLED):
        raise InvalidOrderError(f"Order cannot be cancelled from status {order.status}")
    order.status = ORDER_CANCELLED
    await session.flush()
    return order
