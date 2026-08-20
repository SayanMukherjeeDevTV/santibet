"""Generates trading recommendations with OpenAI, grounded in the signals
already collected by signal_collector.py and recent price history. The
model's output is validated against a strict Pydantic schema before
anything touches the database, and every row lands with
review_status='pending_review' - nothing here is ever user-visible until an
admin approves it via the AI review queue.

NOTE ON MODEL CHOICE: settings.openai_model defaults to a reasonable
current choice, but check OpenAI's docs for whatever they currently
recommend for structured JSON output at the time you deploy this - model
names/availability change over time and this file intentionally reads the
model from config rather than hardcoding it.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.ai import AIRecommendation as AIRecommendationModel, MarketSignal
from app.models.market import Market, MarketOutcome
from app.models.market import PriceHistory

logger = get_logger(__name__)

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You are a market analyst producing a probability-based trading signal for a \
prediction market. You will be given the market question, its current price (as an implied \
probability from 0 to 1), and a list of data points collected from external sources.

Rules:
- Base your reasoning ONLY on the data points provided. Do not invent facts, statistics, or \
events that are not present in the input.
- The `signals` field in your output must be derived from the data points you were given - do \
not fabricate signals.
- Respond with ONLY a single JSON object matching this exact shape, no prose, no markdown fences:
{
  "outcome": "YES" | "NO",
  "confidence": <integer 0-100>,
  "target_price": <float 0-1, your estimate of fair probability>,
  "reasoning": "<string, max 600 characters>",
  "risk_level": "low" | "medium" | "high",
  "timeframe": "<short free-text, e.g. 'Next 7 days'>",
  "signals": [ {"label": "<string>", "value": "<string>", "positive": <bool> }, ... ]
}
"""


class _ModelOutput(BaseModel):
    outcome: str = Field(pattern="^(YES|NO)$")
    confidence: int = Field(ge=0, le=100)
    target_price: float = Field(ge=0, le=1)
    reasoning: str = Field(max_length=600)
    risk_level: str = Field(pattern="^(low|medium|high)$")
    timeframe: str = Field(max_length=60)
    signals: list[dict]


def _client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None,)


async def _gather_context(session: AsyncSession, market: Market) -> tuple[str, list[dict]]:
    signals_stmt = (
        select(MarketSignal)
        .where(MarketSignal.market_id == market.id)
        .order_by(MarketSignal.collected_at.desc())
        .limit(20)
    )
    signals = (await session.execute(signals_stmt)).scalars().all()
    signal_payload = [
        {"source": s.source, "key": s.signal_key, "value": s.value, "collected_at": s.collected_at.isoformat()}
        for s in signals
    ]

    price_stmt = (
        select(PriceHistory)
        .where(PriceHistory.market_id == market.id)
        .order_by(PriceHistory.ts.desc())
        .limit(30)
    )
    prices = (await session.execute(price_stmt)).scalars().all()
    price_summary = ", ".join(f"{p.ts.date()}: {float(p.price):.3f}" for p in reversed(prices))

    user_prompt = (
        f"Market question: {market.question}\n"
        f"Category: {market.category_id}\n"
        f"Description: {market.description}\n"
        f"Recent price history (implied probability of YES): {price_summary or 'no history yet'}\n"
        f"Collected data points: {json.dumps(signal_payload, default=str)}\n"
    )
    return user_prompt, signal_payload


async def generate_recommendation_for_market(session: AsyncSession, market: Market) -> AIRecommendationModel | None:
    outcomes_stmt = select(MarketOutcome).where(MarketOutcome.market_id == market.id)
    outcomes = {o.label: o for o in (await session.execute(outcomes_stmt)).scalars().all()}
    if "YES" not in outcomes:
        logger.warning("recommendation_skipped_no_yes_outcome", market_id=str(market.id))
        return None

    latest_price_stmt = (
        select(PriceHistory.price)
        .where(PriceHistory.outcome_id == outcomes["YES"].id)
        .order_by(PriceHistory.ts.desc())
        .limit(1)
    )
    latest_price_row = (await session.execute(latest_price_stmt)).first()
    current_price = Decimal(str(latest_price_row[0])) if latest_price_row else Decimal("0.5")

    user_prompt, _signal_payload = await _gather_context(session, market)

    client = _client()
    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
    except Exception:
        logger.exception("openai_call_failed", market_id=str(market.id))
        return None

    raw_content = response.choices[0].message.content or "{}"
    usage = response.usage

    try:
        parsed = _ModelOutput.model_validate_json(raw_content)
    except ValidationError:
        logger.warning("ai_output_validation_failed", market_id=str(market.id), raw=raw_content[:500])
        return None

    outcome_row = outcomes.get(parsed.outcome)
    if outcome_row is None:
        logger.warning("ai_output_unknown_outcome", market_id=str(market.id), outcome=parsed.outcome)
        return None

    target_price = Decimal(str(round(parsed.target_price, 4)))
    # Server computes expected_return itself rather than trusting the model's
    # arithmetic: (target - current) / current, expressed as a percentage.
    expected_return = (
        ((target_price - current_price) / current_price * 100) if current_price > 0 else Decimal("0")
    )

    rec = AIRecommendationModel(
        id=uuid.uuid4(),
        market_id=market.id,
        outcome_id=outcome_row.id,
        confidence=parsed.confidence,
        current_price=current_price,
        target_price=target_price,
        expected_return=expected_return,
        reasoning=parsed.reasoning,
        risk_level=parsed.risk_level,
        timeframe=parsed.timeframe,
        signals=parsed.signals,
        model_name=settings.openai_model,
        prompt_version=PROMPT_VERSION,
        input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        output_tokens=getattr(usage, "completion_tokens", 0) or 0,
        review_status="pending_review",
        created_at=datetime.now(timezone.utc),
    )
    session.add(rec)
    await session.flush()
    return rec


async def generate_recommendations_for_active_markets(session: AsyncSession, limit: int = 25) -> int:
    from app.models.market import STATUS_ACTIVE

    stmt = select(Market).where(Market.status == STATUS_ACTIVE, Market.review_status == "approved").limit(limit)
    markets = (await session.execute(stmt)).scalars().all()

    generated = 0
    for market in markets:
        try:
            rec = await generate_recommendation_for_market(session, market)
            if rec is not None:
                generated += 1
        except Exception:
            logger.exception("recommendation_generation_failed", market_id=str(market.id))
    return generated
