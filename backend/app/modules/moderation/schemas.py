from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.listings.models import ListingStatus


class ModerationActionResponse(BaseModel):
    listing_id: UUID
    from_status: ListingStatus
    to_status: ListingStatus
    reason: str | None = None
    logged: bool = True
    updated_at: datetime


class RejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)

