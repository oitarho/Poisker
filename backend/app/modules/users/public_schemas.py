from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class PublicUserProfile(BaseModel):
    id: UUID
    full_name: str | None
    is_phone_verified: bool
    rating: float
    reviews_count: int

