from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateReviewRequest(BaseModel):
    target_user_id: UUID
    listing_id: UUID | None = None
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(default=None, max_length=2000)


class ReviewOut(BaseModel):
    id: UUID
    reviewer_id: UUID
    target_user_id: UUID
    listing_id: UUID | None
    rating: int
    text: str | None
    created_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewOut] = Field(default_factory=list)

