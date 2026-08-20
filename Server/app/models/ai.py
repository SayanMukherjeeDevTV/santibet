from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPKMixin

REVIEW_PENDING = "pending_review"
REVIEW_APPROVED = "approved"
REVIEW_REJECTED = "rejected"


class MarketSignal(Base):
    __tablename__ = "market_signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), nullable=True
    )
    category_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    signal_key: Mapped[str] = mapped_column(String(60), nullable=False)
    value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (Index("ix_market_signals_market_collected", "market_id", "collected_at"),)


class AIRecommendation(UUIDPKMixin, Base):
    __tablename__ = "ai_recommendations"

    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), nullable=False
    )
    outcome_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("market_outcomes.id", ondelete="CASCADE"), nullable=False
    )
    confidence: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    current_price: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    target_price: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    expected_return: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    reasoning: Mapped[str] = mapped_column(String(600), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(10), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(60), nullable=False)
    signals: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    model_name: Mapped[str] = mapped_column(String(60), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)
    input_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(nullable=False, default=0)

    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default=REVIEW_PENDING, index=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AIMarketDraft(UUIDPKMixin, Base):
    __tablename__ = "ai_market_drafts"

    question: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[str] = mapped_column(String(30), ForeignKey("categories.id"), nullable=False)
    proposed_end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_source: Mapped[str] = mapped_column(Text, nullable=False)
    resolution_criteria: Mapped[str] = mapped_column(Text, nullable=False)

    model_name: Mapped[str] = mapped_column(String(60), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), nullable=False)

    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default=REVIEW_PENDING, index=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_market_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
