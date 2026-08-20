from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.market import Category, Market as MarketModel, MarketReport, STATUS_ACTIVE
from app.models.user import User
from app.schemas.common import Page
from app.schemas.market import CategoryInfo, Market, MarketReportRequest, PlatformStats
from app.services import market_view_service

router = APIRouter()
categories_router = APIRouter()
stats_router = APIRouter()

RANGE_MAP = {
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
    "90d": timedelta(days=90),
    "all": timedelta(days=3650),
}


def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


def _decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        return 0


@router.get("", response_model=Page[Market])
async def list_markets(
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    search: str | None = Query(default=None),
    sort: str = Query(default="newest", pattern="^(volume|newest|ending_soon)$"),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    offset = _decode_cursor(cursor)

    stmt = select(MarketModel).where(MarketModel.review_status == "approved")
    if category:
        stmt = stmt.where(MarketModel.category_id == category)
    if status_filter:
        stmt = stmt.where(MarketModel.status == status_filter)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(MarketModel.question.ilike(like), MarketModel.description.ilike(like)))

    if sort == "ending_soon":
        stmt = stmt.order_by(MarketModel.end_date.asc())
    elif sort == "newest":
        stmt = stmt.order_by(MarketModel.created_at.desc())
    # "volume" sort is applied client-side of the DB via market_stats join in
    # a real deployment; kept simple here (newest) to avoid an extra join on
    # every list call - swap in `.order_by(MarketStats.total_volume.desc())`
    # with a join once volume-sorted browsing is a priority.

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.offset(offset).limit(limit)
    markets = (await session.execute(stmt)).scalars().all()

    items = [await market_view_service.build_market(session, m, history_range=timedelta(days=7)) for m in markets]
    next_cursor = _encode_cursor(offset + limit) if offset + limit < total else None
    return Page[Market](items=items, next_cursor=next_cursor, total=total)


@router.get("/featured", response_model=list[Market])
async def featured_markets(session: AsyncSession = Depends(get_db)):
    stmt = (
        select(MarketModel)
        .where(MarketModel.featured.is_(True), MarketModel.status == STATUS_ACTIVE, MarketModel.review_status == "approved")
        .order_by(MarketModel.created_at.desc())
        .limit(10)
    )
    markets = (await session.execute(stmt)).scalars().all()
    return [await market_view_service.build_market(session, m, history_range=timedelta(days=7)) for m in markets]


@router.get("/{slug}", response_model=Market)
async def get_market(
    slug: str, range: str = Query(default="90d", alias="range"), session: AsyncSession = Depends(get_db)
):
    stmt = select(MarketModel).where(MarketModel.slug == slug)
    market = (await session.execute(stmt)).scalar_one_or_none()
    if market is None or market.review_status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")
    history_range = RANGE_MAP.get(range, RANGE_MAP["90d"])
    return await market_view_service.build_market(session, market, history_range=history_range)


@router.post("/{slug}/report", status_code=status.HTTP_201_CREATED)
async def report_market(
    slug: str,
    body: MarketReportRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(MarketModel).where(MarketModel.slug == slug)
    market = (await session.execute(stmt)).scalar_one_or_none()
    if market is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    session.add(
        MarketReport(
            market_id=market.id,
            reported_by=user.id,
            reason=body.reason,
            created_at=datetime.now(timezone.utc),
        )
    )
    await session.flush()
    return {"detail": "Report submitted"}


@categories_router.get("", response_model=list[CategoryInfo])
async def list_categories(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(Category))
    return [CategoryInfo.model_validate(c) for c in result.scalars().all()]


@stats_router.get("", response_model=PlatformStats)
async def platform_stats(session: AsyncSession = Depends(get_db)):
    total_markets = (await session.execute(select(func.count()).select_from(MarketModel))).scalar_one()
    active_markets = (
        await session.execute(
            select(func.count()).select_from(MarketModel).where(MarketModel.status == STATUS_ACTIVE)
        )
    ).scalar_one()
    from app.models.market import MarketStats
    from app.models.user import User as UserModel

    total_volume_row = (await session.execute(select(func.sum(MarketStats.total_volume)))).scalar_one()
    total_traders = (await session.execute(select(func.count()).select_from(UserModel))).scalar_one()

    return PlatformStats(
        total_markets=total_markets,
        active_markets=active_markets,
        total_volume=float(total_volume_row or 0),
        total_traders=total_traders,
    )
