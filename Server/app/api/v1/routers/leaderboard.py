from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.models.admin import LeaderboardSnapshot
from app.models.user import User, ROLE_USER
from app.schemas.leaderboard import LeaderboardEntry

router = APIRouter()


@router.get("", response_model=list[LeaderboardEntry])
async def get_leaderboard(limit: int = Query(default=100, ge=1, le=500), session: AsyncSession = Depends(get_db)):
    stmt = (
        select(LeaderboardSnapshot, User)
        .join(User, User.id == LeaderboardSnapshot.user_id)
        .where(User.role == ROLE_USER)
        .order_by(LeaderboardSnapshot.rank.asc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        LeaderboardEntry(
            rank=snap.rank,
            user_id=user.id,
            name=user.name,
            avatar_url=user.avatar_url or "",
            portfolio_value=float(snap.portfolio_value),
            total_pnl=float(snap.total_pnl),
            total_pnl_percent=float(snap.total_pnl_percent),
            volume=float(snap.volume),
            markets_traded=snap.markets_traded,
            win_rate=float(snap.win_rate),
        )
        for snap, user in rows
    ]
