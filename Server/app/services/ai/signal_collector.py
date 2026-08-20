"""Collects external signals (price/news/economic data) into the
market_signals table, which the recommendation engine reads from. Each
provider is a small adapter implementing a common interface so sources can
be added or swapped independently, and each call is retried with backoff
via tenacity since these are third-party HTTP calls.

None of these providers require an API key to do *something* useful in dev
(CoinGecko's public endpoints are keyless); NewsAPI/FRED need a key set in
.env or they're skipped gracefully.
"""
from __future__ import annotations

import abc
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger
from app.models.market import Category, Market
from app.models.ai import MarketSignal

logger = get_logger(__name__)

HTTP_TIMEOUT = 10.0


class SignalProvider(abc.ABC):
    name: str

    @abc.abstractmethod
    async def fetch(self, market: Market) -> list[dict]:
        """Returns a list of {signal_key, value} dicts."""

    @abc.abstractmethod
    def applies_to(self, category_id: str) -> bool:
        ...


class CoinGeckoProvider(SignalProvider):
    name = "coingecko"

    _SYMBOL_MAP = {"btc": "bitcoin", "bitcoin": "bitcoin", "eth": "ethereum", "ethereum": "ethereum"}

    def applies_to(self, category_id: str) -> bool:
        return category_id == "crypto"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def fetch(self, market: Market) -> list[dict]:
        coin_id = None
        text = f"{market.question} {' '.join(market.tags)}".lower()
        for token, cg_id in self._SYMBOL_MAP.items():
            if token in text:
                coin_id = cg_id
                break
        if not coin_id:
            return []

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin_id, "vs_currencies": "usd", "include_24hr_change": "true"},
            )
            resp.raise_for_status()
            data = resp.json().get(coin_id, {})

        if not data:
            return []
        return [
            {"signal_key": f"{coin_id}_spot_price_usd", "value": {"price": data.get("usd")}},
            {"signal_key": f"{coin_id}_24h_change_pct", "value": {"change_pct": data.get("usd_24h_change")}},
        ]


class FredProvider(SignalProvider):
    name = "fred"

    def applies_to(self, category_id: str) -> bool:
        return category_id == "economy"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def fetch(self, market: Market) -> list[dict]:
        if not settings.fred_api_key:
            logger.info("fred_skipped_no_api_key")
            return []
        # Federal funds rate as a representative macro signal; extend with
        # more series ids as needed (CPI = CPIAUCSL, unemployment = UNRATE).
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": "FEDFUNDS",
                    "api_key": settings.fred_api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 1,
                },
            )
            resp.raise_for_status()
            obs = resp.json().get("observations", [])
        if not obs:
            return []
        return [{"signal_key": "fed_funds_rate", "value": {"rate": obs[0].get("value"), "date": obs[0].get("date")}}]


class NewsAPIProvider(SignalProvider):
    name = "newsapi"

    def applies_to(self, category_id: str) -> bool:
        return True  # relevant to every category

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def fetch(self, market: Market) -> list[dict]:
        if not settings.newsapi_key:
            logger.info("newsapi_skipped_no_api_key")
            return []
        query = market.question[:200]
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.get(
                "https://newsapi.org/v2/everything",
                params={"q": query, "sortBy": "publishedAt", "pageSize": 5, "apiKey": settings.newsapi_key},
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
        return [
            {
                "signal_key": "recent_headline",
                "value": {"title": a.get("title"), "source": (a.get("source") or {}).get("name"), "url": a.get("url")},
            }
            for a in articles[:5]
        ]


ALL_PROVIDERS: list[SignalProvider] = [CoinGeckoProvider(), FredProvider(), NewsAPIProvider()]


async def collect_signals_for_market(session: AsyncSession, market: Market) -> int:
    count = 0
    now = datetime.now(timezone.utc)
    for provider in ALL_PROVIDERS:
        if not provider.applies_to(market.category_id):
            continue
        try:
            signals = await provider.fetch(market)
        except Exception:
            logger.exception("signal_provider_failed", provider=provider.name, market_id=str(market.id))
            continue
        for s in signals:
            session.add(
                MarketSignal(
                    market_id=market.id,
                    category_id=market.category_id,
                    source=provider.name,
                    signal_key=s["signal_key"],
                    value=s["value"],
                    collected_at=now,
                )
            )
            count += 1
    await session.flush()
    return count
