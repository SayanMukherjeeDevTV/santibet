from __future__ import annotations

from uuid import UUID

from app.schemas.common import CamelModel


class LeaderboardEntry(CamelModel):
    """Matches client/lib/types.ts `LeaderboardEntry`."""

    rank: int
    user_id: UUID
    name: str
    avatar_url: str = ""
    portfolio_value: float
    total_pnl: float
    total_pnl_percent: float
    volume: float
    markets_traded: int
    win_rate: float
