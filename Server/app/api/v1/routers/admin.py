from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import client_ip, get_admin_user, get_db
from app.models.ai import AIMarketDraft, AIRecommendation, REVIEW_PENDING
from app.models.market import Market as MarketModel, MarketReport, MarketStats
from app.models.user import User
from app.models.wallet import Account, OWNER_USER
from app.schemas.admin import (
    AdminMarket,
    AdminUser,
    AdminUserUpdateRequest,
    AuditLogEntry,
    ReportOut,
    ReportUpdateRequest,
)
from app.schemas.ai import AIMarketDraftOut, AIReviewDecisionRequest, AIReviewQueueItem
from app.schemas.common import Page
from app.schemas.market import MarketResolveRequest, MarketUpdateRequest
from app.services import admin_service, resolution_service, wallet_service
from app.api.v1.routers.ai import _to_schema as _recommendation_to_schema

router = APIRouter()


# ---------------------------------------------------------------------------
# Markets
# ---------------------------------------------------------------------------

@router.get("/markets", response_model=Page[AdminMarket])
async def admin_list_markets(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    total = (await session.execute(select(func.count()).select_from(MarketModel))).scalar_one()
    stmt = select(MarketModel).order_by(MarketModel.created_at.desc()).offset(offset).limit(limit)
    markets = (await session.execute(stmt)).scalars().all()

    items = []
    for m in markets:
        stats = await session.get(MarketStats, m.id)
        reported_stmt = select(func.count()).select_from(MarketReport).where(
            MarketReport.market_id == m.id, MarketReport.status == "open"
        )
        reported_count = (await session.execute(reported_stmt)).scalar_one()
        items.append(
            AdminMarket(
                id=m.id,
                question=m.question,
                category=m.category_id,
                status=m.status,
                volume=float(stats.total_volume) if stats else 0.0,
                trader_count=stats.trader_count if stats else 0,
                created_at=m.created_at,
                reported=reported_count > 0,
                featured=m.featured,
            )
        )
    return Page[AdminMarket](items=items, total=total, next_cursor=None)


@router.patch("/markets/{market_id}", response_model=AdminMarket)
async def admin_update_market(
    market_id: uuid.UUID,
    body: MarketUpdateRequest,
    request_ip: str = Depends(client_ip),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    market = await session.get(MarketModel, market_id)
    if market is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    before = {"question": market.question, "status": market.status, "featured": market.featured}
    if body.question is not None:
        market.question = body.question
    if body.category is not None:
        market.category_id = body.category
    if body.status is not None:
        market.status = body.status
    if body.featured is not None:
        market.featured = body.featured
    if body.description is not None:
        market.description = body.description
    if body.tags is not None:
        market.tags = body.tags
    await session.flush()

    await admin_service.write_audit_log(
        session,
        actor_user_id=admin.id,
        action="market.update",
        target_type="market",
        target_id=str(market.id),
        before=before,
        after={"question": market.question, "status": market.status, "featured": market.featured},
        ip=request_ip,
    )

    stats = await session.get(MarketStats, market.id)
    return AdminMarket(
        id=market.id,
        question=market.question,
        category=market.category_id,
        status=market.status,
        volume=float(stats.total_volume) if stats else 0.0,
        trader_count=stats.trader_count if stats else 0,
        created_at=market.created_at,
        reported=False,
        featured=market.featured,
    )


@router.post("/markets/{market_id}/resolve")
async def admin_resolve_market(
    market_id: uuid.UUID,
    body: MarketResolveRequest,
    request_ip: str = Depends(client_ip),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    from sqlalchemy.orm import selectinload

    stmt = (
        select(MarketModel)
        .options(selectinload(MarketModel.outcomes))
        .where(MarketModel.id == market_id)
        .with_for_update()
    )
    market = (await session.execute(stmt)).scalar_one_or_none()
    if market is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market not found")

    try:
        result = await resolution_service.resolve_market(session, market, body.winning_outcome_id, admin.id)
    except resolution_service.MarketAlreadyResolvedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except resolution_service.InvalidOutcomeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await admin_service.write_audit_log(
        session,
        actor_user_id=admin.id,
        action="market.resolve",
        target_type="market",
        target_id=str(market.id),
        after={k: str(v) for k, v in result.items()},
        ip=request_ip,
    )
    return {k: (str(v) if not isinstance(v, int) else v) for k, v in result.items()}


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

@router.get("/users", response_model=Page[AdminUser])
async def admin_list_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    total = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    stmt = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    users = (await session.execute(stmt)).scalars().all()

    items = []
    for u in users:
        account = (
            await session.execute(
                select(Account).where(Account.owner_type == OWNER_USER, Account.owner_id == u.id)
            )
        ).scalar_one_or_none()
        balance = await wallet_service.get_balance(session, account.id) if account else 0
        items.append(
            AdminUser(
                id=u.id,
                name=u.name,
                email=u.email,
                balance=float(balance),
                volume=0.0,  # sourced from leaderboard_snapshot in a full deployment
                status=u.account_status,
                joined_at=u.created_at,
                verified=u.is_verified,
            )
        )
    return Page[AdminUser](items=items, total=total, next_cursor=None)


@router.patch("/users/{user_id}", response_model=AdminUser)
async def admin_update_user(
    user_id: uuid.UUID,
    body: AdminUserUpdateRequest,
    request_ip: str = Depends(client_ip),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    before = {"status": target.account_status, "verified": target.is_verified}
    if body.status is not None:
        target.account_status = body.status
    if body.verified is not None:
        target.is_verified = body.verified
    await session.flush()

    await admin_service.write_audit_log(
        session,
        actor_user_id=admin.id,
        action="user.update",
        target_type="user",
        target_id=str(target.id),
        before=before,
        after={"status": target.account_status, "verified": target.is_verified},
        ip=request_ip,
    )

    account = (
        await session.execute(select(Account).where(Account.owner_type == OWNER_USER, Account.owner_id == target.id))
    ).scalar_one_or_none()
    balance = await wallet_service.get_balance(session, account.id) if account else 0
    return AdminUser(
        id=target.id, name=target.name, email=target.email, balance=float(balance), volume=0.0,
        status=target.account_status, joined_at=target.created_at, verified=target.is_verified,
    )


# ---------------------------------------------------------------------------
# AI review queue
# ---------------------------------------------------------------------------

@router.get("/ai-review/queue", response_model=list[AIReviewQueueItem])
async def ai_review_queue(admin: User = Depends(get_admin_user), session: AsyncSession = Depends(get_db)):
    from app.models.market import Market as MarketModel_, MarketOutcome

    rec_stmt = (
        select(AIRecommendation, MarketModel_, MarketOutcome.label)
        .join(MarketModel_, MarketModel_.id == AIRecommendation.market_id)
        .join(MarketOutcome, MarketOutcome.id == AIRecommendation.outcome_id)
        .where(AIRecommendation.review_status == REVIEW_PENDING)
        .order_by(AIRecommendation.created_at.desc())
    )
    rec_rows = (await session.execute(rec_stmt)).all()

    draft_stmt = (
        select(AIMarketDraft).where(AIMarketDraft.review_status == REVIEW_PENDING).order_by(AIMarketDraft.created_at.desc())
    )
    draft_rows = (await session.execute(draft_stmt)).scalars().all()

    items: list[AIReviewQueueItem] = []
    for rec, market, label in rec_rows:
        items.append(
            AIReviewQueueItem(
                item_type="recommendation",
                recommendation=_recommendation_to_schema(rec, market, label),
                created_at=rec.created_at,
            )
        )
    for draft in draft_rows:
        items.append(
            AIReviewQueueItem(
                item_type="market_draft",
                market_draft=AIMarketDraftOut(
                    id=draft.id,
                    question=draft.question,
                    category=draft.category_id,
                    proposed_end_date=draft.proposed_end_date,
                    description=draft.description,
                    resolution_source=draft.resolution_source,
                    resolution_criteria=draft.resolution_criteria,
                    model_name=draft.model_name,
                    created_at=draft.created_at,
                ),
                created_at=draft.created_at,
            )
        )
    items.sort(key=lambda i: i.created_at, reverse=True)
    return items


@router.post("/ai-review/{item_type}/{item_id}/approve")
async def approve_ai_item(
    item_type: str,
    item_id: uuid.UUID,
    body: AIReviewDecisionRequest,
    request_ip: str = Depends(client_ip),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    if item_type == "recommendation":
        rec = await session.get(AIRecommendation, item_id)
        if rec is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
        await admin_service.approve_recommendation(session, rec, admin.id, body.note)
        await admin_service.write_audit_log(
            session, actor_user_id=admin.id, action="ai_recommendation.approve", target_type="ai_recommendation",
            target_id=str(item_id), ip=request_ip,
        )
        return {"id": str(item_id), "status": "approved"}

    elif item_type == "market_draft":
        draft = await session.get(AIMarketDraft, item_id)
        if draft is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Market draft not found")
        draft.review_status = "approved"
        draft.reviewed_by = admin.id
        from datetime import datetime, timezone

        draft.reviewed_at = datetime.now(timezone.utc)
        draft.review_note = body.note
        market = await admin_service.instantiate_market_from_draft(session, draft)
        await admin_service.write_audit_log(
            session, actor_user_id=admin.id, action="ai_market_draft.approve", target_type="ai_market_draft",
            target_id=str(item_id), after={"created_market_id": str(market.id)}, ip=request_ip,
        )
        return {"id": str(item_id), "status": "approved", "market_id": str(market.id), "market_slug": market.slug}

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="item_type must be 'recommendation' or 'market_draft'")


@router.post("/ai-review/{item_type}/{item_id}/reject")
async def reject_ai_item(
    item_type: str,
    item_id: uuid.UUID,
    body: AIReviewDecisionRequest,
    request_ip: str = Depends(client_ip),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    model = AIRecommendation if item_type == "recommendation" else AIMarketDraft if item_type == "market_draft" else None
    if model is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="item_type must be 'recommendation' or 'market_draft'")

    item = await session.get(model, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    await admin_service.reject_item(session, item, admin.id, body.note)
    await admin_service.write_audit_log(
        session, actor_user_id=admin.id, action=f"{item_type}.reject", target_type=item_type, target_id=str(item_id), ip=request_ip,
    )
    return {"id": str(item_id), "status": "rejected"}


# ---------------------------------------------------------------------------
# Audit log & reports
# ---------------------------------------------------------------------------

@router.get("/audit-log", response_model=Page[AuditLogEntry])
async def get_audit_log(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    from app.models.admin import AuditLog

    total = (await session.execute(select(func.count()).select_from(AuditLog))).scalar_one()
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    items = [
        AuditLogEntry(
            id=r.id, actor_user_id=r.actor_user_id, action=r.action, target_type=r.target_type,
            target_id=r.target_id, before=r.before, after=r.after, ip=str(r.ip) if r.ip else None,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page[AuditLogEntry](items=items, total=total, next_cursor=None)


@router.get("/reports", response_model=list[ReportOut])
async def list_reports(admin: User = Depends(get_admin_user), session: AsyncSession = Depends(get_db)):
    stmt = (
        select(MarketReport, MarketModel)
        .join(MarketModel, MarketModel.id == MarketReport.market_id)
        .order_by(MarketReport.created_at.desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        ReportOut(
            id=r.id, market_id=m.id, market_slug=m.slug, question=m.question, reported_by=r.reported_by,
            reason=r.reason, status=r.status, created_at=r.created_at,
        )
        for r, m in rows
    ]


@router.patch("/reports/{report_id}", response_model=ReportOut)
async def update_report(
    report_id: uuid.UUID,
    body: ReportUpdateRequest,
    admin: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
):
    report = await session.get(MarketReport, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    report.status = body.status
    await session.flush()
    market = await session.get(MarketModel, report.market_id)
    return ReportOut(
        id=report.id, market_id=market.id, market_slug=market.slug, question=market.question,
        reported_by=report.reported_by, reason=report.reason, status=report.status, created_at=report.created_at,
    )
