"""Shared fixtures.

Tests run against a REAL Postgres database (settings.database_url_test) -
not SQLite - because the schema leans on Postgres-specific types (JSONB,
ARRAY, NUMERIC precision, partial unique indexes) that don't have faithful
SQLite equivalents, and this is a money-handling system where "close enough"
isn't good enough.

Before running tests:  createdb santibet_test   (see README)

Each test gets a fresh transaction that is rolled back afterwards, so tests
never see each other's data and the test DB stays empty between runs.
"""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.market import Category
from app.models.user import ROLE_ADMIN, ROLE_USER, User


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(settings.database_url_test, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    connection = await test_engine.connect()
    trans = await connection.begin()
    session_factory = async_sessionmaker(
        bind=connection, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    session = session_factory()
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await connection.close()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def seed_categories(db_session: AsyncSession) -> None:
    db_session.add(Category(id="crypto", label="Crypto", icon="bitcoin", color="#f59e0b", description="Crypto markets"))
    db_session.add(Category(id="politics", label="Politics", icon="landmark", color="#ef4444", description="Politics"))
    await db_session.flush()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="trader@example.com",
        password_hash=hash_password("CorrectHorse123!"),
        name="Test Trader",
        role=ROLE_USER,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        email="admin@example.com",
        password_hash=hash_password("CorrectHorse123!"),
        name="Test Admin",
        role=ROLE_ADMIN,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


def auth_headers_for(user: User) -> dict:
    token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    return auth_headers_for(test_user)


@pytest.fixture
def admin_headers(admin_user: User) -> dict:
    return auth_headers_for(admin_user)
