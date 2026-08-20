from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import CamelModel


class AdminMarket(CamelModel):
    """Matches client/lib/types.ts `AdminMarket`."""

    id: UUID
    question: str
    category: str
    status: str
    volume: float
    trader_count: int
    created_at: datetime
    reported: bool
    featured: bool = False


class AdminUser(CamelModel):
    """Matches client/lib/types.ts `AdminUser`."""

    id: UUID
    name: str
    email: str
    balance: float
    volume: float
    status: str  # active | suspended | banned
    joined_at: datetime
    verified: bool


class AdminUserUpdateRequest(CamelModel):
    status: str | None = None  # active | suspended | banned
    verified: bool | None = None


class AuditLogEntry(CamelModel):
    id: int
    actor_user_id: UUID | None
    action: str
    target_type: str | None
    target_id: str | None
    before: dict | list | None = None
    after: dict | list | None = None
    ip: str | None = None
    created_at: datetime


class ReportOut(CamelModel):
    id: UUID
    market_id: UUID
    market_slug: str
    question: str
    reported_by: UUID
    reason: str
    status: str
    created_at: datetime


class ReportUpdateRequest(CamelModel):
    status: str  # open | dismissed | resolved
