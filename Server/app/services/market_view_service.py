"""Builds the `Market` response shape (matching client/lib/types.ts exactly)
from a Market row plus its outcomes, live AMM prices, cached stats, and
price history. Kept separate from the router so both the list and detail
endpoints - and the WS layer - can reuse the same assembly logic.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import Market as MarketModel, MarketOutcome, MarketStats, PriceHistory
from app.models.trading import AMMPool, Trade
from app.schemas.market import BinaryPricePoint, Market, MarketOutcomeData, PricePoint, SparklinePoint
from app.services.trading_engine import amm
from app.services.trading_engine.router import load_pool_quantities

DEFAULT_HISTORY_RANGE = timedelta(days=90)
SPARKLINE_POINTS = 24


async def _current_prices(session: AsyncSession, market_id) -> dict:
    pool = await session.get(AMMPool, market_id)
    if pool is None:
        return {}
    q = load_pool_quantities(pool)
    b = Decimal(str(pool.liquidity_param))
    return {k: v for k, v in amm.prices(q, b).items()}


async def _outcome_volume(session: AsyncSession, outcome_id) -> Decimal:
    stmt = select(Trade.price, Trade.shares).where(Trade.outcome_id == outcome_id)
    rows = (await session.execute(stmt)).all()
    return sum((Decimal(str(p)) * Decimal(str(s)) for p, s in rows), Decimal("0"))


async def _price_history_for_outcome(
    session: AsyncSession, outcome_id, since: datetime
) -> list[PricePoint]:
    stmt = (
        select(PriceHistory.ts, PriceHistory.price)
        .where(PriceHistory.outcome_id == outcome_id, PriceHistory.ts >= since)
        .order_by(PriceHistory.ts.asc())
    )
    rows = (await session.execute(stmt)).all()
    return [PricePoint(t=ts, price=float(price)) for ts, price in rows]


async def build_market(
    session: AsyncSession, market: MarketModel, *, history_range: timedelta = DEFAULT_HISTORY_RANGE
) -> Market:
    since = datetime.now(timezone.utc) - history_range

    outcomes_stmt = select(MarketOutcome).where(MarketOutcome.market_id == market.id).order_by(MarketOutcome.seq)
    outcome_rows = (await session.execute(outcomes_stmt)).scalars().all()

    live_prices = await _current_prices(session, market.id)

    outcome_data: list[MarketOutcomeData] = []
    yes_history: list[PricePoint] = []
    for o in outcome_rows:
        price = float(live_prices.get(str(o.id), Decimal("0.5")))
        volume = await _outcome_volume(session, o.id)
        history = await _price_history_for_outcome(session, o.id, since)
        if o.label == "YES":
            yes_history = history
        outcome_data.append(
            MarketOutcomeData(
                id=o.id,
                label=o.label,
                price=price,
                probability=price,
                volume=float(volume),
                price_history=history,
            )
        )

    combined_history = [
        BinaryPricePoint(t=p.t, yes=p.price, no=round(1 - p.price, 6)) for p in yes_history
    ]
    sparkline = [
        SparklinePoint(t=p.t, v=p.price) for p in yes_history[-SPARKLINE_POINTS:]
    ]

    stats = await session.get(MarketStats, market.id)
    liquidity = float(stats.liquidity) if stats else 0.0
    total_volume = float(stats.total_volume) if stats else 0.0
    volume_24h = float(stats.volume_24h) if stats else 0.0
    trader_count = stats.trader_count if stats else 0

    return Market(
        id=market.id,
        slug=market.slug,
        question=market.question,
        category=market.category_id,
        status=market.status,
        end_date=market.end_date,
        liquidity=liquidity,
        total_volume=total_volume,
        volume_24h=volume_24h,
        trader_count=trader_count,
        image=market.image_url,
        outcomes=outcome_data,
        price_history=combined_history,
        tags=market.tags or [],
        description=market.description,
        resolution_source=market.resolution_source,
        featured=market.featured,
        sparkline_data=sparkline,
    )
