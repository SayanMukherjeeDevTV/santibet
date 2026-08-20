from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import CamelModel


class WalletBalance(CamelModel):
    balance: float
    currency: str = "USD"
    pending_withdrawals: float = 0
    real_money_enabled: bool


class Transaction(CamelModel):
    """Matches client/lib/types.ts `Transaction`."""

    id: UUID
    type: str  # deposit | withdrawal | buy | sell | payout | fee
    market_id: UUID | None = None
    market_slug: str | None = None
    question: str | None = None
    amount: float
    balance_after: float
    status: str  # completed | pending | failed
    created_at: datetime


class DepositRequest(CamelModel):
    method: str = Field(pattern="^(card|bank|crypto)$")
    amount: float = Field(gt=0, le=1_000_000)


class DepositResponse(CamelModel):
    payment_id: UUID
    status: str
    client_secret: str | None = None       # Stripe PaymentIntent client secret (card/bank)
    crypto_deposit_address: str | None = None
    crypto_currency: str | None = None


class WithdrawRequest(CamelModel):
    method: str = Field(pattern="^(bank|crypto)$")
    amount: float = Field(gt=0)
    destination: str | None = None  # bank account token / crypto address


class WithdrawResponse(CamelModel):
    payment_id: UUID
    status: str


class Position(CamelModel):
    """Matches client/lib/types.ts `Position`."""

    id: UUID
    market_id: UUID
    market_slug: str
    question: str
    outcome: str
    shares: float
    avg_price: float
    current_price: float
    invested: float
    current_value: float
    pnl: float
    pnl_percent: float
    status: str
    opened_at: datetime
