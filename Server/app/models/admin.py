from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    """Append-only. The application DB role should only have INSERT
    privileges on this table (see deploy/grants.sql)."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    before: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LeaderboardSnapshot(Base):
    """Refreshed periodically by a Celery beat job; GET /leaderboard reads
    straight from this table instead of aggregating live."""

    __tablename__ = "leaderboard_snapshot"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    rank: Mapped[int] = mapped_column(nullable=False, index=True)
    portfolio_value: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total_pnl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total_pnl_percent: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    markets_traded: Mapped[int] = mapped_column(nullable=False, default=0)
    win_rate: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
