from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.rate_limit import enforce_rate_limit
from app.models.market import Market as MarketModel
from app.models.trading import ORDER_OPEN, ORDER_PARTIALLY_FILLED, Order, Trade
from app.models.user import User
from app.schemas.trading import (
    FillLeg,
    OpenOrder,
    OrderBookEntry,
    OrderBookResponse,
    OrderCreateRequest,
    OrderResponse,
    TradeHistoryEntry,
)
from app.services import trading_service
from app.services.trading_engine.order_book import build_book_levels, get_resting_orders

router = APIRouter()


async def _resolve_market_by_slug(session: AsyncSession, slug: str) -> MarketModel:
    stmt = select(MarketModel).where(MarketModel.slug == slug)
    market = (await session.execute(stmt)).scalar_one_or_none()
    if market is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    return market


@router.post("/markets/{slug}/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    slug: str,
    body: OrderCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    await enforce_rate_limit(f"place-order:{user.id}", limit=30, window_seconds=60)

    market = await _resolve_market_by_slug(session, slug)

    from decimal import Decimal

    try:
        order = await trading_service.place_order(
            session,
            user_id=user.id,
            market=market,
            outcome_id=body.outcome_id,
            side=body.side,
            order_type=body.order_type,
            time_in_force=body.time_in_force,
            shares=Decimal(str(body.shares)) if body.shares is not None else None,
            amount=Decimal(str(body.amount)) if body.amount is not None else None,
            limit_price=Decimal(str(body.limit_price)) if body.limit_price is not None else None,
            idempotency_key=idempotency_key,
        )
    except trading_service.MarketNotTradableError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except trading_service.InvalidOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except trading_service.FillOrKillError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    avg_price = None
    if order.shares_filled and Decimal(str(order.shares_filled)) > 0:
        trades_stmt = select(Trade).where(Trade.taker_order_id == order.id)
        trades = (await session.execute(trades_stmt)).scalars().all()
        total_cost = sum((Decimal(str(t.price)) * Decimal(str(t.shares)) for t in trades), Decimal("0"))
        total_shares = sum((Decimal(str(t.shares)) for t in trades), Decimal("0"))
        avg_price = float(total_cost / total_shares) if total_shares > 0 else None
        fills = [FillLeg(source=t.fill_source, price=float(t.price), shares=float(t.shares)) for t in trades]
    else:
        fills = []

    return OrderResponse(
        id=order.id,
        market_id=order.market_id,
        outcome_id=order.outcome_id,
        side=order.side,
        order_type=order.order_type,
        status=order.status,
        shares_requested=float(order.shares_requested),
        shares_filled=float(order.shares_filled),
        avg_fill_price=avg_price,
        limit_price=float(order.limit_price) if order.limit_price is not None else None,
        fills=fills,
        created_at=order.created_at,
    )


@router.delete("/orders/{order_id}", status_code=status.HTTP_200_OK)
async def cancel_order(
    order_id: uuid.UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)
):
    try:
        order = await trading_service.cancel_order(session, user.id, order_id)
    except trading_service.InvalidOrderError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"id": str(order.id), "status": order.status}


@router.get("/orders", response_model=list[OpenOrder])
async def list_my_orders(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    stmt = (
        select(Order, MarketModel)
        .join(MarketModel, MarketModel.id == Order.market_id)
        .where(Order.user_id == user.id, Order.status.in_([ORDER_OPEN, ORDER_PARTIALLY_FILLED]))
        .order_by(Order.created_at.desc())
    )
    rows = (await session.execute(stmt)).all()

    from app.models.market import MarketOutcome

    result: list[OpenOrder] = []
    for order, market in rows:
        outcome = await session.get(MarketOutcome, order.outcome_id)
        result.append(
            OpenOrder(
                id=order.id,
                market_id=market.id,
                market_slug=market.slug,
                question=market.question,
                outcome_id=order.outcome_id,
                outcome_label=outcome.label if outcome else "",
                side=order.side,
                order_type=order.order_type,
                limit_price=float(order.limit_price) if order.limit_price is not None else None,
                shares_requested=float(order.shares_requested),
                shares_filled=float(order.shares_filled),
                status=order.status,
                created_at=order.created_at,
            )
        )
    return result


@router.get("/markets/{slug}/orderbook", response_model=OrderBookResponse)
async def get_order_book(slug: str, outcome: str = Query(default="YES"), session: AsyncSession = Depends(get_db)):
    market = await _resolve_market_by_slug(session, slug)

    from app.models.market import MarketOutcome
    from app.models.trading import SIDE_BUY, SIDE_SELL

    outcome_stmt = select(MarketOutcome).where(MarketOutcome.market_id == market.id, MarketOutcome.label == outcome)
    outcome_row = (await session.execute(outcome_stmt)).scalar_one_or_none()
    if outcome_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outcome not found")

    bid_orders = await get_resting_orders(session, market.id, outcome_row.id, SIDE_BUY)
    ask_orders = await get_resting_orders(session, market.id, outcome_row.id, SIDE_SELL)

    bid_levels = sorted(build_book_levels(bid_orders), key=lambda l: l.price, reverse=True)
    ask_levels = sorted(build_book_levels(ask_orders), key=lambda l: l.price)

    def _cumulative(levels) -> list[OrderBookEntry]:
        running = 0.0
        out = []
        for level in levels:
            running += float(level.size)
            out.append(OrderBookEntry(price=float(level.price), size=float(level.size), total=running))
        return out

    return OrderBookResponse(bids=_cumulative(bid_levels), asks=_cumulative(ask_levels))


@router.get("/markets/{slug}/trades", response_model=list[TradeHistoryEntry])
async def get_trade_history(
    slug: str, limit: int = Query(default=50, ge=1, le=200), session: AsyncSession = Depends(get_db)
):
    market = await _resolve_market_by_slug(session, slug)

    from app.models.market import MarketOutcome

    stmt = (
        select(Trade, MarketOutcome.label)
        .join(MarketOutcome, MarketOutcome.id == Trade.outcome_id)
        .where(Trade.market_id == market.id)
        .order_by(Trade.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        TradeHistoryEntry(
            id=trade.id, price=float(trade.price), size=float(trade.shares), outcome=label, time=trade.created_at, side=trade.taker_side
        )
        for trade, label in rows
    ]
