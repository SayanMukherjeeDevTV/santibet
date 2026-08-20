from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import UUIDPKMixin

OWNER_USER = "user"
OWNER_PLATFORM_TREASURY = "platform_treasury"
OWNER_PLATFORM_FEES = "platform_fees"
OWNER_PAYMENT_CLEARING = "payment_clearing"

DIRECTION_DEBIT = "debit"
DIRECTION_CREDIT = "credit"

PAYMENT_DEPOSIT = "deposit"
PAYMENT_WITHDRAWAL = "withdrawal"

PAYMENT_PENDING = "pending"
PAYMENT_COMPLETED = "completed"
PAYMENT_FAILED = "failed"
PAYMENT_REVERSED = "reversed"
PAYMENT_HELD = "held"


class Account(UUIDPKMixin, Base):
    __tablename__ = "accounts"

    owner_type: Mapped[str] = mapped_column(String(30), nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")

    __table_args__ = (
        UniqueConstraint("owner_type", "owner_id", "currency", name="uq_accounts_owner_currency"),
    )


class LedgerEntry(Base):
    """Append-only double-entry ledger. Balance for an account is always
    derived as SUM(credit) - SUM(debit) over this table - never stored as a
    mutable column. The application DB role should have INSERT-only grants
    on this table (no UPDATE/DELETE) - see deploy/grants.sql."""

    __tablename__ = "ledger_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_group_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String(6), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    reason: Mapped[str] = mapped_column(String(30), nullable=False)
    ref_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ref_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint("amount > 0", name="positive_amount"),
        Index("ix_ledger_entries_account_id", "account_id"),
        Index("ix_ledger_entries_transaction_group_id", "transaction_group_id"),
        Index("ix_ledger_entries_ref", "ref_type", "ref_id"),
    )


class Payment(UUIDPKMixin, Base):
    __tablename__ = "payments"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String(12), nullable=False)
    method: Mapped[str] = mapped_column(String(12), nullable=False)  # card | bank | crypto | demo
    processor: Mapped[str] = mapped_column(String(20), nullable=False)  # stripe | crypto | demo
    processor_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(12), nullable=False, default=PAYMENT_PENDING)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_payments_user_id", "user_id"),)
