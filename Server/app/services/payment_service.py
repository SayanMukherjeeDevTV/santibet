"""Payment processor integration.

Real-money deposits/withdrawals go through Stripe (card + bank/ACH) or a
pluggable crypto adapter. When settings.platform_real_money_enabled is
False, both paths are bypassed in favor of a demo/paper-money path that
credits the ledger directly - see wallet router for how this flag is
consulted.

Stripe and the crypto provider are wrapped behind small interfaces so a
different processor can be swapped in later without touching callers.
"""
from __future__ import annotations

import abc
import uuid
from decimal import Decimal

import stripe as stripe_sdk

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

stripe_sdk.api_key = settings.stripe_secret_key


class PaymentProviderError(Exception):
    pass


# ---------------------------------------------------------------------------
# Stripe (card + bank/ACH)
# ---------------------------------------------------------------------------

class StripeProvider:
    async def create_deposit_intent(self, *, user_id: uuid.UUID, amount: Decimal, currency: str = "usd") -> dict:
        """Creates a Stripe PaymentIntent for a card or ACH deposit. Returns
        {processor_ref, client_secret}. The frontend confirms the intent
        client-side; POST /webhooks/stripe finalizes it server-side."""
        if not settings.stripe_secret_key:
            raise PaymentProviderError("Stripe is not configured (STRIPE_SECRET_KEY missing)")
        intent = stripe_sdk.PaymentIntent.create(
            amount=int(amount * 100),  # Stripe uses minor units (cents)
            currency=currency,
            metadata={"user_id": str(user_id)},
            automatic_payment_methods={"enabled": True},
        )
        return {"processor_ref": intent["id"], "client_secret": intent["client_secret"]}

    async def create_payout(self, *, user_id: uuid.UUID, amount: Decimal, destination: str) -> dict:
        """Initiates a payout to a previously-verified bank destination
        (Stripe Connect external account / payout). Returns {processor_ref}.
        """
        if not settings.stripe_secret_key:
            raise PaymentProviderError("Stripe is not configured (STRIPE_SECRET_KEY missing)")
        payout = stripe_sdk.Payout.create(
            amount=int(amount * 100),
            currency="usd",
            destination=destination,
            metadata={"user_id": str(user_id)},
        )
        return {"processor_ref": payout["id"]}

    def verify_webhook(self, payload: bytes, sig_header: str) -> dict:
        if not settings.stripe_webhook_secret:
            raise PaymentProviderError("STRIPE_WEBHOOK_SECRET is not configured")
        event = stripe_sdk.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
        return event


# ---------------------------------------------------------------------------
# Crypto (pluggable - dev fake by default; swap in Coinbase Commerce/BitGo/etc.)
# ---------------------------------------------------------------------------

class CryptoPaymentProvider(abc.ABC):
    @abc.abstractmethod
    async def create_deposit_address(self, *, user_id: uuid.UUID, currency: str) -> dict:
        """Returns {address, currency, processor_ref}."""

    @abc.abstractmethod
    async def check_deposit_status(self, processor_ref: str) -> dict:
        """Returns {status, amount} - status in pending|completed|failed."""

    @abc.abstractmethod
    async def initiate_payout(self, *, user_id: uuid.UUID, amount: Decimal, destination_address: str) -> dict:
        """Returns {processor_ref, status}."""


class DevFakeCryptoProvider(CryptoPaymentProvider):
    """Dev-mode stand-in so the deposit/withdraw flow is fully exercisable
    without a real crypto processor account. NEVER use in production -
    replace with a real adapter (Coinbase Commerce, BitGo, etc.) implementing
    the same interface before enabling real-money crypto."""

    async def create_deposit_address(self, *, user_id: uuid.UUID, currency: str) -> dict:
        fake_address = f"dev-{currency.lower()}-{uuid.uuid4().hex[:24]}"
        logger.warning("dev_fake_crypto_provider_used", action="create_deposit_address", user_id=str(user_id))
        return {"address": fake_address, "currency": currency, "processor_ref": fake_address}

    async def check_deposit_status(self, processor_ref: str) -> dict:
        return {"status": "pending", "amount": None}

    async def initiate_payout(self, *, user_id: uuid.UUID, amount: Decimal, destination_address: str) -> dict:
        logger.warning("dev_fake_crypto_provider_used", action="initiate_payout", user_id=str(user_id))
        return {"processor_ref": f"dev-payout-{uuid.uuid4().hex[:24]}", "status": "pending"}


def get_crypto_provider() -> CryptoPaymentProvider:
    # Swap this for a real provider once one is configured; kept as a single
    # seam so the rest of the codebase never imports a concrete provider.
    return DevFakeCryptoProvider()


def get_stripe_provider() -> StripeProvider:
    return StripeProvider()
