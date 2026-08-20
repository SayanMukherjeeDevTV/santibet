from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.common import CamelModel
from app.schemas.user import UserMe


class SignupRequest(CamelModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class AccessTokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    user: UserMe


class ForgotPasswordRequest(CamelModel):
    email: EmailStr


class ResetPasswordRequest(CamelModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class VerifyEmailRequest(CamelModel):
    token: str
