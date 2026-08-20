"""Celery application: background jobs for AI generation, signal ingestion,
leaderboard refresh, and payment/payout reconciliation.

Run the worker with:   celery -A app.core.celery_app worker --loglevel=info
Run the beat scheduler: celery -A app.core.celery_app beat --loglevel=info
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "santibet",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=5 * 60,
    task_soft_time_limit=4 * 60,
)

celery_app.conf.beat_schedule = {
    "collect-market-signals": {
        "task": "app.workers.tasks.collect_market_signals_task",
        "schedule": crontab(minute="*/30"),
    },
    "generate-ai-recommendations": {
        "task": "app.workers.tasks.generate_ai_recommendations_task",
        "schedule": crontab(minute=0, hour="*/3"),
    },
    "generate-ai-market-drafts": {
        "task": "app.workers.tasks.generate_ai_market_drafts_task",
        "schedule": crontab(minute=0, hour=6),
    },
    "refresh-leaderboard": {
        "task": "app.workers.tasks.refresh_leaderboard_task",
        "schedule": crontab(minute="*/5"),
    },
    "refresh-market-stats": {
        "task": "app.workers.tasks.refresh_market_stats_task",
        "schedule": crontab(minute="*/5"),
    },
    "expire-stale-markets": {
        "task": "app.workers.tasks.expire_stale_markets_task",
        "schedule": crontab(minute=0),
    },
}
