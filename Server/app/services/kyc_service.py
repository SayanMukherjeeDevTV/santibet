"""KYC (identity verification) integration, pluggable behind a small
interface so a real provider (Persona, Onfido, Stripe Identity, ...) can be
dropped in later without touching callers. The dev fake auto-approves after
being started, purely so the rest of the app (withdrawal gating, admin
views) can be built and tested end-to-end today.

NEVER use DevFakeKYCProvider in production - real-money withdrawals must be
gated on a real identity verification result.
"""
from __future__ import annotations

import abc
import uuid

from app.core.logging import get_logger

logger = get_logger(__name__)


class KYCProvider(abc.ABC):
    @abc.abstractmethod
    async def start_verification(self, *, user_id: uuid.UUID) -> dict:
        """Returns {session_id, redirect_url|None}."""

    @abc.abstractmethod
    def parse_webhook(self, payload: dict) -> dict:
        """Returns {user_id, status} where status in pending|approved|rejected."""


class DevFakeKYCProvider(KYCProvider):
    async def start_verification(self, *, user_id: uuid.UUID) -> dict:
        logger.warning("dev_fake_kyc_provider_used", action="start_verification", user_id=str(user_id))
        return {"session_id": f"dev-kyc-{uuid.uuid4().hex[:24]}", "redirect_url": None}

    def parse_webhook(self, payload: dict) -> dict:
        return {"user_id": payload.get("user_id"), "status": payload.get("status", "approved")}


def get_kyc_provider() -> KYCProvider:
    return DevFakeKYCProvider()
