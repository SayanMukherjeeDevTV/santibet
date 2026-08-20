from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPKMixin

POSITION_OPEN = "open"
POSITION_WON = "won"
POSITION_LOST = "lost"
POSITION_SOLD = "sold"


class Position(UUIDPKMixin, Base):
    __tablename__ = "positions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="RESTRICT"), nullable=False
    )
    outcome_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("market_outcomes.id", ondelete="RESTRICT"), nullable=False
    )
    shares: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False, default=0)
    avg_price: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    invested: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default=POSITION_OPEN, index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payout_idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    __table_args__ = (
        Index(
            "uq_positions_open_per_user_market_outcome",
            "user_id",
            "market_id",
            "outcome_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )
