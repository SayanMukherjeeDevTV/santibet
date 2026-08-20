"""FastAPI application factory. Run with:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

import time
import uuid

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitExceeded
from app.core.redis import close_redis, get_redis
from app.db.session import engine
from app.services.position_service import InsufficientSharesError
from app.services.wallet_service import InsufficientFundsError, LedgerImbalanceError

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="SantiBet API",
        version="1.0.0",
        description="Backend API for SantiBet prediction markets.",
        docs_url="/docs" if not settings.is_prod else None,
        redoc_url="/redoc" if not settings.is_prod else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        start = time.perf_counter()
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id, path=request.url.path, method=request.method)
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("unhandled_exception")
            raise
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_completed", status_code=response.status_code, duration_ms=duration_ms)
        return response

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_prod:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    # --- Exception handlers: consistent {"error": {...}} envelope ---

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": "rate_limited", "message": exc.detail, "details": None}},
            headers=exc.headers,
        )

    @app.exception_handler(InsufficientFundsError)
    async def _insufficient_funds_handler(request: Request, exc: InsufficientFundsError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": {"code": "insufficient_funds", "message": str(exc), "details": None}},
        )

    @app.exception_handler(InsufficientSharesError)
    async def _insufficient_shares_handler(request: Request, exc: InsufficientSharesError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": {"code": "insufficient_shares", "message": str(exc), "details": None}},
        )

    @app.exception_handler(LedgerImbalanceError)
    async def _ledger_imbalance_handler(request: Request, exc: LedgerImbalanceError):
        logger.error("ledger_imbalance_detected", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "internal_error", "message": "Something went wrong.", "details": None}},
        )

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "internal_error", "message": "Something went wrong.", "details": None}},
        )

    @app.get("/health", tags=["system"])
    async def health():
        db_ok = True
        redis_ok = True
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception:
            db_ok = False
        try:
            await get_redis().ping()
        except Exception:
            redis_ok = False
        healthy = db_ok and redis_ok
        return JSONResponse(
            status_code=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "ok" if healthy else "degraded", "database": db_ok, "redis": redis_ok},
        )

    @app.on_event("shutdown")
    async def _shutdown():
        await close_redis()
        await engine.dispose()

    app.include_router(api_router, prefix="/v1")

    return app


app = create_app()
