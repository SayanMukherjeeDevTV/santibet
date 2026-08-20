from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel


class UserPublic(CamelModel):
    """Matches client/lib/types.ts `User` exactly."""

    id: UUID
    name: str
    email: EmailStr
    avatar_url: str = ""
    balance: float
    portfolio_value: float
    total_pnl: float
    total_pnl_percent: float
    rank: int
    joined_at: datetime
    verified: bool
    role: str


class UserMe(UserPublic):
    """Superset returned only to the authenticated user themself - adds
    account/compliance fields the frontend profile page can use but that
    should never be exposed for other users."""

    kyc_status: str
    account_status: str
    is_real_money_eligible: bool
    region_code: str | None = None


class UserUpdateRequest(CamelModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    avatar_url: str | None = None
    region_code: str | None = Field(default=None, max_length=10)
