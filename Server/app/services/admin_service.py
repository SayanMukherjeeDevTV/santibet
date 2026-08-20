from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.admin import AuditLog
from app.models.ai import AIMarketDraft, AIRecommendation, REVIEW_APPROVED, REVIEW_REJECTED
from app.models.market import Market, MarketOutcome, MarketStats, SOURCE_AI_GENERATED, STATUS_ACTIVE
from app.models.trading import AMMPool
from app.services.trading_engine.amm import initial_quantities, max_subsidy_loss


async def write_audit_log(
    session: AsyncSession,
    *,
    actor_user_id: uuid.UUID | None,
    action: str,
    target_type: str | None = None,
    target_id: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
    ip: str | None = None,
) -> None:
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before=before,
            after=after,
            ip=ip,
            created_at=datetime.now(timezone.utc),
        )
    )
    await session.flush()


def _slugify(question: str, suffix: str) -> str:
    import re

    base = re.sub(r"[^a-z0-9]+", "-", question.lower()).strip("-")[:80]
    return f"{base}-{suffix}"


async def instantiate_market_from_draft(
    session: AsyncSession, draft: AIMarketDraft, *, liquidity_param: float | None = None
) -> Market:
    """Creates the real, live Market + YES/NO MarketOutcome rows + a
    seeded AMMPool from an approved AI draft. Never called except from the
    admin approve endpoint."""
    market_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    b = Decimal(str(liquidity_param or settings.default_amm_liquidity_param))

    market = Market(
        id=market_id,
        slug=_slugify(draft.question, market_id.hex[:8]),
        question=draft.question,
        category_id=draft.category_id,
        status=STATUS_ACTIVE,
        end_date=draft.proposed_end_date,
        description=draft.description,
        resolution_source=draft.resolution_source,
        resolution_criteria=draft.resolution_criteria,
        featured=False,
        tags=[],
        created_by=None,
        source=SOURCE_AI_GENERATED,
        review_status=REVIEW_APPROVED,
    )
    session.add(market)

    yes_outcome = MarketOutcome(id=uuid.uuid4(), market_id=market_id, label="YES", seq=0)
    no_outcome = MarketOutcome(id=uuid.uuid4(), market_id=market_id, label="NO", seq=1)
    session.add_all([yes_outcome, no_outcome])

    pool = AMMPool(
        market_id=market_id,
        liquidity_param=b,
        outcome_shares={k: str(v) for k, v in initial_quantities([str(yes_outcome.id), str(no_outcome.id)]).items()},
        subsidy_remaining=max_subsidy_loss(b, 2),
        created_at=now,
        updated_at=now,
    )
    session.add(pool)

    session.add(
        MarketStats(market_id=market_id, liquidity=float(b), total_volume=0, volume_24h=0, trader_count=0, updated_at=now)
    )

    # Flush inserts (Market, MarketOutcome, AMMPool, MarketStats) first to avoid foreign key errors on ai_market_drafts
    await session.flush()

    draft.created_market_id = market_id
    await session.flush()
    return market


async def approve_recommendation(session: AsyncSession, rec: AIRecommendation, reviewer_id: uuid.UUID, note: str | None) -> None:
    rec.review_status = REVIEW_APPROVED
    rec.reviewed_by = reviewer_id
    rec.reviewed_at = datetime.now(timezone.utc)
    rec.review_note = note
    await session.flush()


async def reject_item(session, item, reviewer_id: uuid.UUID, note: str | None) -> None:
    item.review_status = REVIEW_REJECTED
    item.reviewed_by = reviewer_id
    item.reviewed_at = datetime.now(timezone.utc)
    item.review_note = note
    await session.flush()
