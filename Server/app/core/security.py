"""Password hashing and JWT helpers.

Access tokens are short-lived and stateless. Refresh tokens are long-lived,
opaque, rotated on use, and stored server-side (hashed) in the refresh_tokens
table so they can be revoked - see app/services/auth_service.py.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings

_hasher = PasswordHasher()

TokenType = Literal["access", "refresh"]


def hash_password(raw_password: str) -> str:
    return _hasher.hash(raw_password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, raw_password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(user_id: UUID, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None


def generate_opaque_token() -> str:
    """A cryptographically random token used for refresh tokens, email
    verification links, password reset links, and WS tickets. Only the hash
    of this value is ever persisted."""
    return secrets.token_urlsafe(48)


def hash_opaque_token(token: str) -> str:
    # Refresh/reset tokens are high-entropy already; a fast hash is fine here
    # (unlike passwords, these are not vulnerable to offline brute force).
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()
