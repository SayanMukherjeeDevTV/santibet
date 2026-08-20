from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.market import Market as MarketModel
from app.models.position import Position as PositionModel
from app.models.trading import AMMPool
from app.models.user import User
from app.schemas.wallet import Position
from app.services.trading_engine import amm as amm_math
from app.services.trading_engine.router import load_pool_quantities

router = APIRouter()


@router.get("/users/me/positions", response_model=list[Position])
async def list_my_positions(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    stmt = (
        select(PositionModel, MarketModel)
        .join(MarketModel, MarketModel.id == PositionModel.market_id)
        .where(PositionModel.user_id == user.id)
        .order_by(PositionModel.opened_at.desc())
    )
    rows = (await session.execute(stmt)).all()

    from app.models.market import MarketOutcome

    # Cache AMM prices per market within this request to avoid recomputing
    # per position when a user holds multiple outcomes of the same market.
    pool_price_cache: dict = {}

    result: list[Position] = []
    for position, market in rows:
        if market.id not in pool_price_cache:
            pool = await session.get(AMMPool, market.id)
            if pool is not None:
                q = load_pool_quantities(pool)
                b = Decimal(str(pool.liquidity_param))
                pool_price_cache[market.id] = amm_math.prices(q, b)
            else:
                pool_price_cache[market.id] = {}

        outcome = await session.get(MarketOutcome, position.outcome_id)
        current_price = pool_price_cache[market.id].get(str(position.outcome_id), Decimal(str(position.avg_price)))

        shares = Decimal(str(position.shares))
        invested = Decimal(str(position.invested))
        current_value = shares * current_price
        pnl = current_value - invested
        pnl_percent = (pnl / invested * 100) if invested > 0 else Decimal("0")

        result.append(
            Position(
                id=position.id,
                market_id=market.id,
                market_slug=market.slug,
                question=market.question,
                outcome=outcome.label if outcome else "",
                shares=float(shares),
                avg_price=float(position.avg_price),
                current_price=float(current_price),
                invested=float(invested),
                current_value=float(current_value),
                pnl=float(pnl),
                pnl_percent=float(pnl_percent),
                status=position.status,
                opened_at=position.opened_at,
            )
        )
    return result
