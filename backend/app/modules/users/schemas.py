from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

_PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")


class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None
    phone_number: str | None
    is_email_verified: bool
    is_phone_verified: bool
    rating: float
    reviews_count: int
    created_at: datetime
    updated_at: datetime


class UpdateMyProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=200)
    phone_number: str | None = Field(default=None, max_length=32)
    clear_phone_number: bool = False

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        vv = v.strip()
        if vv == "":
            return None
        if not _PHONE_RE.match(vv):
            raise ValueError("Phone number must be in E.164 format, e.g. +79991234567")
        return vv

