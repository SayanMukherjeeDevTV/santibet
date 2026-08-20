"""Auth service: signup/login/refresh/logout.

Refresh tokens are rotating and stored hashed. Each refresh token belongs to
a `family_id`; using a refresh token issues a new one in the same family and
revokes the old one. If an already-revoked (i.e. already-used) token is
presented again, that's a signal the token was stolen/replayed, so the
*entire family* is revoked and the caller must log in again.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.models.user import ACCOUNT_ACTIVE, ACCOUNT_BANNED, ACCOUNT_SUSPENDED, RefreshToken, User
from app.services import wallet_service


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AccountNotActiveError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def signup(session: AsyncSession, *, name: str, email: str, password: str) -> User:
    email = normalize_email(email)
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise EmailAlreadyRegisteredError(f"{email} is already registered")

    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        name=name.strip(),
    )
    session.add(user)
    await session.flush()

    # Every user gets a cash account created up front so wallet reads never
    # have to special-case "account doesn't exist yet".
    await wallet_service.get_or_create_user_account(session, user.id)

    return user


async def authenticate(session: AsyncSession, *, email: str, password: str) -> User:
    email = normalize_email(email)
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Invalid email or password")
    if user.account_status in (ACCOUNT_SUSPENDED, ACCOUNT_BANNED):
        raise AccountNotActiveError(f"Account is {user.account_status}")
    return user


async def issue_token_pair(
    session: AsyncSession, user: User, *, user_agent: str | None, ip: str | None
) -> tuple[str, str]:
    """Returns (access_token, raw_refresh_token). Starts a new refresh token
    family."""
    access_token = create_access_token(user.id, user.role)

    raw_refresh = generate_opaque_token()
    now = datetime.now(timezone.utc)
    session.add(
        RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=hash_opaque_token(raw_refresh),
            family_id=uuid.uuid4(),
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip=ip,
            created_at=now,
        )
    )
    await session.flush()
    return access_token, raw_refresh


async def rotate_refresh_token(
    session: AsyncSession, raw_refresh_token: str, *, user_agent: str | None, ip: str | None
) -> tuple[str, str]:
    """Validates + rotates a refresh token. Returns a new (access_token,
    raw_refresh_token) pair. Raises InvalidRefreshTokenError on any problem
    (expired, revoked, reused, unknown)."""
    token_hash = hash_opaque_token(raw_refresh_token)
    result = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()
    if token_row is None:
        raise InvalidRefreshTokenError("Unknown refresh token")

    now = datetime.now(timezone.utc)
    if token_row.revoked_at is not None:
        # Reuse of an already-rotated token: treat as compromise, kill the
        # whole family so a stolen token can't keep refreshing forever.
        await session.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == token_row.family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.flush()
        raise InvalidRefreshTokenError("Refresh token reuse detected; all sessions revoked")

    if token_row.expires_at < now:
        raise InvalidRefreshTokenError("Refresh token expired")

    user = await session.get(User, token_row.user_id)
    if user is None or user.account_status in (ACCOUNT_SUSPENDED, ACCOUNT_BANNED):
        raise InvalidRefreshTokenError("Account is not active")

    token_row.revoked_at = now

    access_token = create_access_token(user.id, user.role)
    raw_new_refresh = generate_opaque_token()
    session.add(
        RefreshToken(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=hash_opaque_token(raw_new_refresh),
            family_id=token_row.family_id,
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip=ip,
            created_at=now,
        )
    )
    await session.flush()
    return access_token, raw_new_refresh


async def revoke_refresh_token(session: AsyncSession, raw_refresh_token: str) -> None:
    token_hash = hash_opaque_token(raw_refresh_token)
    result = await session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    token_row = result.scalar_one_or_none()
    if token_row is not None and token_row.revoked_at is None:
        token_row.revoked_at = datetime.now(timezone.utc)
        await session.flush()
