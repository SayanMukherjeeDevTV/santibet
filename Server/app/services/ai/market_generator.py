"""Generates NEW market proposals with OpenAI (e.g. from trending news
headlines per category) and stores them as ai_market_drafts rows. Nothing
here ever creates a live `markets` row directly - an admin must approve the
draft via POST /admin/ai-review/{id}/approve, which is what actually
instantiates the Market + MarketOutcome + AMMPool rows (see
app/api/v1/routers/admin.py).
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.ai import AIMarketDraft
from app.models.market import Category

logger = get_logger(__name__)

PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You propose new prediction market questions for a trading platform. Given a \
category, propose 1-3 well-formed markets. Each must be:
- Objectively resolvable: a neutral third party could determine the outcome from public \
information by the resolution date, with no ambiguity.
- Phrased as a yes/no question.
- Given a concrete resolution_source (what publicly checkable source determines the outcome) and \
resolution_criteria (the exact, unambiguous rule used to resolve YES vs NO).
- Given a proposed_end_date between 3 and 180 days from now (ISO 8601 date).

Respond with ONLY a JSON object, no prose, no markdown fences, matching exactly:
{
  "markets": [
    {
      "question": "<string>",
      "description": "<1-3 sentence string>",
      "resolution_source": "<string>",
      "resolution_criteria": "<string>",
      "proposed_end_date": "<ISO 8601 date, e.g. 2026-12-31>"
    }
  ]
}
"""


class _DraftItem(BaseModel):
    question: str = Field(min_length=10, max_length=500)
    description: str = Field(min_length=5, max_length=1000)
    resolution_source: str = Field(min_length=3, max_length=500)
    resolution_criteria: str = Field(min_length=3, max_length=1000)
    proposed_end_date: str


class _ModelOutput(BaseModel):
    markets: list[_DraftItem]


def _client() -> AsyncOpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return AsyncOpenAI(api_key=settings.openai_api_key, base_url=settings.openai_base_url or None,)


async def generate_drafts_for_category(session: AsyncSession, category: Category) -> int:
    client = _client()
    user_prompt = (
        f"Category: {category.label} ({category.id})\n"
        f"Category description: {category.description}\n"
        "Propose markets that would be interesting and timely for traders on this platform. "
        "Do not propose markets about specific named private individuals' personal lives."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
    except Exception:
        logger.exception("openai_market_draft_call_failed", category_id=category.id)
        return 0

    raw_content = response.choices[0].message.content or "{}"
    try:
        parsed = _ModelOutput.model_validate_json(raw_content)
    except ValidationError:
        logger.warning("ai_market_draft_validation_failed", category_id=category.id, raw=raw_content[:500])
        return 0

    now = datetime.now(timezone.utc)
    created = 0
    for item in parsed.markets:
        try:
            end_date = datetime.fromisoformat(item.proposed_end_date).replace(tzinfo=timezone.utc)
        except ValueError:
            end_date = now + timedelta(days=30)

        # Guardrails independent of what the model claims: clamp to [3, 180] days out.
        min_end, max_end = now + timedelta(days=3), now + timedelta(days=180)
        end_date = min(max(end_date, min_end), max_end)

        session.add(
            AIMarketDraft(
                id=uuid.uuid4(),
                question=item.question,
                category_id=category.id,
                proposed_end_date=end_date,
                description=item.description,
                resolution_source=item.resolution_source,
                resolution_criteria=item.resolution_criteria,
                model_name=settings.openai_model,
                prompt_version=PROMPT_VERSION,
                review_status="pending_review",
                created_at=now,
            )
        )
        created += 1

    await session.flush()
    return created


async def generate_drafts_for_all_categories(session: AsyncSession) -> int:
    from sqlalchemy import select

    categories = (await session.execute(select(Category))).scalars().all()
    total = 0
    for category in categories:
        try:
            total += await generate_drafts_for_category(session, category)
        except Exception:
            logger.exception("market_draft_generation_failed", category_id=category.id)
    return total
