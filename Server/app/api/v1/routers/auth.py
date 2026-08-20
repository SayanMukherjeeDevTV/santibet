from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import client_ip, get_current_user, get_db
from app.core.rate_limit import enforce_rate_limit
from app.core.security import (
    create_access_token,
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
)
from app.models.user import EmailVerificationToken, PasswordResetToken, User
from app.schemas.auth import (
    AccessTokenResponse,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    VerifyEmailRequest,
)
from app.services import auth_service, user_view_service

router = APIRouter()

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, raw_refresh: str) -> None:
    from app.core.config import settings

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=raw_refresh,
        httponly=True,
        secure=settings.is_prod,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/v1/auth",
    )


@router.post("/signup", response_model=AccessTokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    body: SignupRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    ip = client_ip(request)
    await enforce_rate_limit(f"signup:{ip}", limit=5, window_seconds=900)

    try:
        user = await auth_service.signup(session, name=body.name, email=body.email, password=body.password)
    except auth_service.EmailAlreadyRegisteredError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")

    access_token, raw_refresh = await auth_service.issue_token_pair(
        session, user, user_agent=request.headers.get("user-agent"), ip=ip
    )
    _set_refresh_cookie(response, raw_refresh)
    user_me = await user_view_service.build_user_me(session, user)
    return AccessTokenResponse(access_token=access_token, user=user_me)


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    ip = client_ip(request)
    await enforce_rate_limit(f"login:{ip}:{body.email.lower()}", limit=5, window_seconds=900)

    try:
        user = await auth_service.authenticate(session, email=body.email, password=body.password)
    except auth_service.InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    except auth_service.AccountNotActiveError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    access_token, raw_refresh = await auth_service.issue_token_pair(
        session, user, user_agent=request.headers.get("user-agent"), ip=ip
    )
    _set_refresh_cookie(response, raw_refresh)
    user_me = await user_view_service.build_user_me(session, user)
    return AccessTokenResponse(access_token=access_token, user=user_me)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    ip = client_ip(request)
    try:
        access_token, raw_new_refresh = await auth_service.rotate_refresh_token(
            session, refresh_token, user_agent=request.headers.get("user-agent"), ip=ip
        )
    except auth_service.InvalidRefreshTokenError as e:
        response.delete_cookie(REFRESH_COOKIE, path="/v1/auth")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    _set_refresh_cookie(response, raw_new_refresh)

    import uuid as _uuid

    from app.core.security import decode_token

    decoded = decode_token(access_token)
    user = await session.get(User, _uuid.UUID(decoded["sub"])) if decoded else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    user_me = await user_view_service.build_user_me(session, user)
    return AccessTokenResponse(access_token=access_token, user=user_me)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_COOKIE),
):
    if refresh_token:
        await auth_service.revoke_refresh_token(session, refresh_token)
    response.delete_cookie(REFRESH_COOKIE, path="/v1/auth")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    body: ForgotPasswordRequest, request: Request, session: AsyncSession = Depends(get_db)
):
    await enforce_rate_limit(f"forgot-password:{client_ip(request)}", limit=5, window_seconds=900)

    email = body.email.strip().lower()
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    # Always return 202 regardless of whether the email exists, to avoid
    # leaking which emails are registered.
    if user is not None:
        raw_token = generate_opaque_token()
        now = datetime.now(timezone.utc)
        session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_opaque_token(raw_token),
                expires_at=now + timedelta(hours=1),
                created_at=now,
            )
        )
        await session.flush()
        # TODO: send `raw_token` via the (stubbed) email service - logged
        # here in dev only so the flow is testable end-to-end without SMTP.
        from app.core.logging import get_logger

        get_logger(__name__).info("password_reset_token_issued_dev_only", email=email, token=raw_token)
    return {"detail": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(body: ResetPasswordRequest, session: AsyncSession = Depends(get_db)):
    token_hash = hash_opaque_token(body.token)
    result = await session.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if token_row is None or token_row.used_at is not None or token_row.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = await session.get(User, token_row.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user.password_hash = hash_password(body.new_password)
    token_row.used_at = now
    await session.flush()
    return {"detail": "Password updated"}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(body: VerifyEmailRequest, session: AsyncSession = Depends(get_db)):
    token_hash = hash_opaque_token(body.token)
    result = await session.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
    )
    token_row = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if token_row is None or token_row.used_at is not None or token_row.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = await session.get(User, token_row.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user.is_verified = True
    token_row.used_at = now
    await session.flush()
    return {"detail": "Email verified"}
