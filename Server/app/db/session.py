"""Async engine/session setup. Import `get_db` as a FastAPI dependency to
get an AsyncSession scoped to a single request; the session is committed on
clean exit and rolled back on exception."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

from sqlalchemy.pool import NullPool

engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,
)


AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
