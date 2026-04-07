from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=200)
    phone_number: str | None = Field(default=None, max_length=32)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserMe(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    phone_number: str | None
    is_email_verified: bool
    email_verified_at: datetime | None
    is_phone_verified: bool
    rating: float
    reviews_count: int
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    tokens: TokenPair
    user: UserMe


class VerifyEmailRequestBody(BaseModel):
    """When not authenticated, provide email to resend verification."""

    email: EmailStr | None = None


class VerifyEmailRequestResult(BaseModel):
    status: Literal["sent", "already_verified"]
    message: str


class VerifyEmailConfirmRequest(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")


class VerifyEmailConfirmResult(BaseModel):
    status: Literal["verified", "already_verified"]
    message: str


class PasswordResetRequestBody(BaseModel):
    email: EmailStr


class PasswordResetRequestResult(BaseModel):
    message: str


class PasswordResetConfirmRequest(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetConfirmResult(BaseModel):
    message: str

