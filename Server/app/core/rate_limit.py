"""A small fixed-window rate limiter backed by Redis, used to protect
sensitive endpoints (login, signup, password reset, order placement) from
abuse. Not a general-purpose API gateway rate limiter - just enough to stop
brute force / spam without adding another infra dependency.
"""
from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.core.redis import get_redis


class RateLimitExceeded(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


async def enforce_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    """Fixed-window counter. `key` should already include the identity being
    limited (e.g. f"login:{ip}:{email}")."""
    redis = get_redis()
    redis_key = f"ratelimit:{key}"
    current = await redis.incr(redis_key)
    if current == 1:
        await redis.expire(redis_key, window_seconds)
    if current > limit:
        ttl = await redis.ttl(redis_key)
        raise RateLimitExceeded(retry_after=max(ttl, 1))


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
