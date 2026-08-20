from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

STATUS_UPCOMING = "upcoming"
STATUS_ACTIVE = "active"
STATUS_RESOLVED = "resolved"
STATUS_VOIDED = "voided"

SOURCE_ADMIN = "admin"
SOURCE_AI_GENERATED = "ai_generated"

REVIEW_PENDING = "pending_review"
REVIEW_APPROVED = "approved"
REVIEW_REJECTED = "rejected"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    label: Mapped[str] = mapped_column(String(60), nullable=False)
    icon: Mapped[str] = mapped_column(String(60), nullable=False, default="")
    color: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class Market(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "markets"

    slug: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[str] = mapped_column(String(30), ForeignKey("categories.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=STATUS_UPCOMING, index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    resolution_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(40)), nullable=False, default=list)

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False, default=SOURCE_ADMIN)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default=REVIEW_APPROVED)

    resolved_outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("market_outcomes.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payouts_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    outcomes: Mapped[list["MarketOutcome"]] = relationship(
        back_populates="market",
        cascade="all, delete-orphan",
        foreign_keys="MarketOutcome.market_id",
    )
    category: Mapped["Category"] = relationship()

    __table_args__ = (Index("ix_markets_category_status", "category_id", "status"),)


class MarketOutcome(UUIDPKMixin, Base):
    __tablename__ = "market_outcomes"

    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(20), nullable=False)  # 'YES' | 'NO' (extensible to N-ary)
    seq: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    market: Mapped["Market"] = relationship(back_populates="outcomes", foreign_keys=[market_id])

    __table_args__ = (Index("ix_market_outcomes_market_id", "market_id"),)


class MarketStats(Base):
    __tablename__ = "market_stats"

    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), primary_key=True
    )
    liquidity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    total_volume: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    volume_24h: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    trader_count: Mapped[int] = mapped_column(nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), nullable=False
    )
    outcome_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("market_outcomes.id", ondelete="CASCADE"), nullable=False
    )
    price: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (Index("ix_price_history_market_ts", "market_id", "ts"),)


class MarketReport(UUIDPKMixin, Base):
    __tablename__ = "reports"

    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), nullable=False
    )
    reported_by: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
