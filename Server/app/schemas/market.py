from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import CamelModel


class PricePoint(CamelModel):
    t: datetime
    price: float


class BinaryPricePoint(CamelModel):
    t: datetime
    yes: float
    no: float


class SparklinePoint(CamelModel):
    t: datetime
    v: float


class MarketOutcomeData(CamelModel):
    """Matches client/lib/types.ts `MarketOutcomeData`."""

    id: UUID
    label: str
    price: float
    probability: float
    volume: float
    price_history: list[PricePoint] = Field(default_factory=list)


class Market(CamelModel):
    """Matches client/lib/types.ts `Market` exactly."""

    id: UUID
    slug: str
    question: str
    category: str
    status: str
    end_date: datetime
    liquidity: float
    total_volume: float
    volume_24h: float
    trader_count: int
    image: str | None = None
    outcomes: list[MarketOutcomeData]
    price_history: list[BinaryPricePoint]
    tags: list[str]
    description: str
    resolution_source: str | None = None
    featured: bool | None = None
    sparkline_data: list[SparklinePoint]


class CategoryInfo(CamelModel):
    id: str
    label: str
    icon: str
    color: str
    description: str


class PlatformStats(CamelModel):
    total_markets: int
    active_markets: int
    total_volume: float
    total_traders: int


class MarketCreateRequest(CamelModel):
    question: str = Field(min_length=5, max_length=500)
    category: str
    end_date: datetime
    description: str = ""
    resolution_source: str | None = None
    resolution_criteria: str | None = None
    image: str | None = None
    tags: list[str] = Field(default_factory=list)
    featured: bool = False
    liquidity_param: float | None = None


class MarketUpdateRequest(CamelModel):
    question: str | None = None
    category: str | None = None
    status: str | None = None
    featured: bool | None = None
    description: str | None = None
    tags: list[str] | None = None


class MarketResolveRequest(CamelModel):
    winning_outcome_id: UUID


class MarketReportRequest(CamelModel):
    reason: str = Field(min_length=3, max_length=500)
