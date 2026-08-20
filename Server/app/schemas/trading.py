from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import CamelModel


class OrderBookEntry(CamelModel):
    """Matches client/lib/types.ts `OrderBookEntry`."""

    price: float
    size: float
    total: float


class OrderBookResponse(CamelModel):
    bids: list[OrderBookEntry]
    asks: list[OrderBookEntry]


class TradeHistoryEntry(CamelModel):
    """Matches client/lib/types.ts `TradeHistoryEntry`."""

    id: UUID
    price: float
    size: float
    outcome: str
    time: datetime
    side: str


class OrderCreateRequest(CamelModel):
    outcome_id: UUID
    side: str = Field(pattern="^(buy|sell)$")
    order_type: str = Field(default="market", pattern="^(market|limit)$")
    time_in_force: str = Field(default="GTC", pattern="^(GTC|IOC|FOK)$")
    # Either shares or amount (USD) may be supplied for a buy market order;
    # sells and limit orders must specify shares directly.
    shares: float | None = Field(default=None, gt=0)
    amount: float | None = Field(default=None, gt=0)
    limit_price: float | None = Field(default=None, gt=0, lt=1)


class FillLeg(CamelModel):
    source: str  # order_book | amm
    price: float
    shares: float


class OrderResponse(CamelModel):
    id: UUID
    market_id: UUID
    outcome_id: UUID
    side: str
    order_type: str
    status: str
    shares_requested: float
    shares_filled: float
    avg_fill_price: float | None = None
    limit_price: float | None = None
    fills: list[FillLeg] = Field(default_factory=list)
    created_at: datetime


class OpenOrder(CamelModel):
    id: UUID
    market_id: UUID
    market_slug: str
    question: str
    outcome_id: UUID
    outcome_label: str
    side: str
    order_type: str
    limit_price: float | None
    shares_requested: float
    shares_filled: float
    status: str
    created_at: datetime
