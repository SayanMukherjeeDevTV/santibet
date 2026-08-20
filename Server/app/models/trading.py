from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPKMixin

SIDE_BUY = "buy"
SIDE_SELL = "sell"

ORDER_TYPE_MARKET = "market"
ORDER_TYPE_LIMIT = "limit"

TIF_GTC = "GTC"
TIF_IOC = "IOC"
TIF_FOK = "FOK"

ORDER_OPEN = "open"
ORDER_PARTIALLY_FILLED = "partially_filled"
ORDER_FILLED = "filled"
ORDER_CANCELLED = "cancelled"
ORDER_EXPIRED = "expired"

FILL_SOURCE_BOOK = "order_book"
FILL_SOURCE_AMM = "amm"


class AMMPool(Base):
    """LMSR liquidity pool state for a market. One row per market."""

    __tablename__ = "amm_pools"

    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="CASCADE"), primary_key=True
    )
    liquidity_param: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    # {outcome_id (str): net_shares_issued (str, Decimal-safe)}
    outcome_shares: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    subsidy_remaining: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Order(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="RESTRICT"), nullable=False
    )
    outcome_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("market_outcomes.id", ondelete="RESTRICT"), nullable=False
    )
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)
    time_in_force: Mapped[str] = mapped_column(String(3), nullable=False, default=TIF_GTC)
    limit_price: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    shares_requested: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    shares_filled: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ORDER_OPEN, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)

    __table_args__ = (
        Index("ix_orders_book_lookup", "market_id", "outcome_id", "side", "status", "limit_price"),
        Index("ix_orders_user_id", "user_id"),
    )


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("markets.id", ondelete="RESTRICT"), nullable=False
    )
    outcome_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("market_outcomes.id", ondelete="RESTRICT"), nullable=False
    )
    taker_order_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False
    )
    maker_order_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=True
    )
    fill_source: Mapped[str] = mapped_column(String(12), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    shares: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    taker_side: Mapped[str] = mapped_column(String(4), nullable=False)
    buyer_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    seller_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    fee: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (Index("ix_trades_market_created", "market_id", "created_at"),)
