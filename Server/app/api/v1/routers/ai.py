from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db
from app.models.ai import AIRecommendation as AIRecommendationModel, REVIEW_APPROVED
from app.models.market import Market as MarketModel, MarketOutcome
from app.schemas.ai import AIRecommendation, AISignal

router = APIRouter()


def _to_schema(rec: AIRecommendationModel, market: MarketModel, outcome_label: str) -> AIRecommendation:
    return AIRecommendation(
        id=rec.id,
        market_id=market.id,
        market_slug=market.slug,
        question=market.question,
        category=market.category_id,
        outcome=outcome_label,
        confidence=rec.confidence,
        current_price=float(rec.current_price),
        target_price=float(rec.target_price),
        expected_return=float(rec.expected_return),
        reasoning=rec.reasoning,
        risk_level=rec.risk_level,
        timeframe=rec.timeframe,
        signals=[AISignal(**s) for s in rec.signals],
        created_at=rec.created_at,
    )


@router.get("/recommendations", response_model=list[AIRecommendation])
async def list_recommendations(
    category: str | None = Query(default=None),
    market_slug: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    # Never expose anything short of admin-approved - enforced here, not just
    # by the UI, so there's no way to see pending/rejected AI content by
    # guessing an id or bypassing the frontend.
    stmt = (
        select(AIRecommendationModel, MarketModel, MarketOutcome.label)
        .join(MarketModel, MarketModel.id == AIRecommendationModel.market_id)
        .join(MarketOutcome, MarketOutcome.id == AIRecommendationModel.outcome_id)
        .where(AIRecommendationModel.review_status == REVIEW_APPROVED)
        .order_by(AIRecommendationModel.created_at.desc())
        .limit(limit)
    )
    if category:
        stmt = stmt.where(MarketModel.category_id == category)
    if market_slug:
        stmt = stmt.where(MarketModel.slug == market_slug)

    rows = (await session.execute(stmt)).all()
    return [_to_schema(rec, market, label) for rec, market, label in rows]


@router.get("/recommendations/{recommendation_id}", response_model=AIRecommendation)
async def get_recommendation(recommendation_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    stmt = (
        select(AIRecommendationModel, MarketModel, MarketOutcome.label)
        .join(MarketModel, MarketModel.id == AIRecommendationModel.market_id)
        .join(MarketOutcome, MarketOutcome.id == AIRecommendationModel.outcome_id)
        .where(AIRecommendationModel.id == recommendation_id, AIRecommendationModel.review_status == REVIEW_APPROVED)
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    rec, market, label = row
    return _to_schema(rec, market, label)
