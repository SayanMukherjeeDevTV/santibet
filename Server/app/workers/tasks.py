"""Celery tasks. Celery workers are synchronous by default, so each task
opens its own short-lived asyncio event loop via asyncio.run() around a
single async DB session - simple and correct for the batch-style,
not-latency-sensitive jobs here (signal collection, AI generation,
leaderboard refresh, payout reconciliation).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)


def _run(coro):
    return asyncio.run(coro)


@celery_app.task(name="app.workers.tasks.collect_market_signals_task")
def collect_market_signals_task() -> int:
    return _run(_collect_market_signals())


async def _collect_market_signals() -> int:
    from app.models.market import STATUS_ACTIVE, Market
    from app.services.ai.signal_collector import collect_signals_for_market

    async with AsyncSessionLocal() as session:
        markets = (
            await session.execute(select(Market).where(Market.status == STATUS_ACTIVE))
        ).scalars().all()
        total = 0
        for market in markets:
            total += await collect_signals_for_market(session, market)
        await session.commit()
        logger.info("signals_collected", count=total, markets=len(markets))
        return total


@celery_app.task(name="app.workers.tasks.generate_ai_recommendations_task")
def generate_ai_recommendations_task() -> int:
    return _run(_generate_ai_recommendations())


async def _generate_ai_recommendations() -> int:
    from app.services.ai.recommendation_engine import generate_recommendations_for_active_markets

    async with AsyncSessionLocal() as session:
        count = await generate_recommendations_for_active_markets(session)
        await session.commit()
        logger.info("ai_recommendations_generated", count=count)
        return count


@celery_app.task(name="app.workers.tasks.generate_ai_market_drafts_task")
def generate_ai_market_drafts_task() -> int:
    return _run(_generate_ai_market_drafts())


async def _generate_ai_market_drafts() -> int:
    from app.services.ai.market_generator import generate_drafts_for_all_categories

    async with AsyncSessionLocal() as session:
        count = await generate_drafts_for_all_categories(session)
        await session.commit()
        logger.info("ai_market_drafts_generated", count=count)
        return count


@celery_app.task(name="app.workers.tasks.refresh_leaderboard_task")
def refresh_leaderboard_task() -> int:
    return _run(_refresh_leaderboard())


async def _refresh_leaderboard() -> int:
    from app.services.leaderboard_service import refresh_leaderboard

    async with AsyncSessionLocal() as session:
        count = await refresh_leaderboard(session)
        await session.commit()
        logger.info("leaderboard_refreshed", users=count)
        return count


@celery_app.task(name="app.workers.tasks.refresh_market_stats_task")
def refresh_market_stats_task() -> int:
    return _run(_refresh_market_stats())


async def _refresh_market_stats() -> int:
    """Recomputes volume_24h precisely (the incremental update in
    trading_service is a coarse running total) and trader_count from actual
    trade/position data, correcting any drift."""
    from app.models.market import Market, MarketStats
    from app.models.position import Position
    from app.models.trading import Trade
    from sqlalchemy import func

    since_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as session:
        markets = (await session.execute(select(Market.id))).scalars().all()
        updated = 0
        for market_id in markets:
            vol_24h_row = (
                await session.execute(
                    select(func.sum(Trade.price * Trade.shares)).where(
                        Trade.market_id == market_id, Trade.created_at >= since_24h
                    )
                )
            ).scalar_one()
            trader_count_row = (
                await session.execute(
                    select(func.count(func.distinct(Position.user_id))).where(Position.market_id == market_id)
                )
            ).scalar_one()

            stats = await session.get(MarketStats, market_id)
            if stats is None:
                continue
            stats.volume_24h = Decimal(str(vol_24h_row or 0))
            stats.trader_count = trader_count_row or 0
            stats.updated_at = now
            updated += 1
        await session.commit()
        logger.info("market_stats_refreshed", markets=updated)
        return updated


@celery_app.task(name="app.workers.tasks.expire_stale_markets_task")
def expire_stale_markets_task() -> int:
    return _run(_expire_stale_markets())


async def _expire_stale_markets() -> int:
    """Markets past their end_date that haven't been resolved yet move to
    'upcoming'->'active'->(admin resolves). This job doesn't auto-resolve
    (that requires a real-world outcome, which only an admin/oracle can
    supply) - it just flags them so the admin queue surfaces markets that
    need attention. Kept intentionally conservative."""
    from app.models.market import STATUS_ACTIVE, Market

    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        stmt = select(Market).where(Market.status == STATUS_ACTIVE, Market.end_date < now)
        stale = (await session.execute(stmt)).scalars().all()
        for market in stale:
            logger.info("market_needs_resolution", market_id=str(market.id), slug=market.slug)
        return len(stale)


@celery_app.task(name="app.workers.tasks.process_withdrawal_payout_task", bind=True, max_retries=3)
def process_withdrawal_payout_task(self, payment_id: str, destination: str | None) -> None:
    return _run(_process_withdrawal_payout(payment_id, destination))


async def _process_withdrawal_payout(payment_id: str, destination: str | None) -> None:
    import uuid as _uuid

    from app.models.wallet import PAYMENT_COMPLETED, PAYMENT_FAILED, Payment
    from app.services import payment_service, wallet_service
    from app.models.wallet import OWNER_PAYMENT_CLEARING

    async with AsyncSessionLocal() as session:
        payment = await session.get(Payment, _uuid.UUID(payment_id))
        if payment is None:
            return
        now = datetime.now(timezone.utc)
        try:
            if payment.method == "bank":
                provider = payment_service.get_stripe_provider()
                result = await provider.create_payout(
                    user_id=payment.user_id, amount=Decimal(str(payment.amount)), destination=destination or ""
                )
            else:
                provider = payment_service.get_crypto_provider()
                result = await provider.initiate_payout(
                    user_id=payment.user_id, amount=Decimal(str(payment.amount)), destination_address=destination or ""
                )
            payment.processor_ref = result.get("processor_ref")
            payment.status = PAYMENT_COMPLETED
            payment.updated_at = now
        except Exception as exc:
            logger.exception("withdrawal_payout_failed", payment_id=payment_id)
            payment.status = PAYMENT_FAILED
            payment.failure_reason = str(exc)[:255]
            payment.updated_at = now
            # Refund the held amount back to the user since the payout failed.
            await wallet_service.credit_user(
                session, payment.user_id, Decimal(str(payment.amount)), reason="refund",
                counter_owner_type=OWNER_PAYMENT_CLEARING, ref_type="payment", ref_id=payment.id,
            )
        await session.commit()
