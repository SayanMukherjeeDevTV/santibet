from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import CamelModel


class AISignal(CamelModel):
    label: str
    value: str
    positive: bool


class AIRecommendation(CamelModel):
    """Matches client/lib/types.ts `AIRecommendation` exactly."""

    id: UUID
    market_id: UUID
    market_slug: str
    question: str
    category: str
    outcome: str
    confidence: int
    current_price: float
    target_price: float
    expected_return: float
    reasoning: str
    risk_level: str
    timeframe: str
    signals: list[AISignal]
    created_at: datetime


class AIMarketDraftOut(CamelModel):
    id: UUID
    question: str
    category: str
    proposed_end_date: datetime
    description: str
    resolution_source: str
    resolution_criteria: str
    model_name: str
    created_at: datetime


class AIReviewQueueItem(CamelModel):
    """A discriminated union-ish envelope for the admin review queue, which
    mixes pending recommendations and pending market drafts in one feed."""

    item_type: str  # 'recommendation' | 'market_draft'
    recommendation: AIRecommendation | None = None
    market_draft: AIMarketDraftOut | None = None
    created_at: datetime


class AIReviewDecisionRequest(CamelModel):
    note: str | None = None
