from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.listings.models import ListingKind, ListingStatus


class ListingPhotoOut(BaseModel):
    id: UUID
    key: str
    url: str
    content_type: str | None
    sort_order: int
    created_at: datetime


class ListingOut(BaseModel):
    id: UUID
    kind: ListingKind
    status: ListingStatus
    title: str
    description: str
    price: float
    location_id: UUID
    category_id: UUID
    owner_id: UUID
    published_at: datetime | None
    views_count: int
    favorites_count: int
    boost_score: float
    photos: list[ListingPhotoOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ListingListResponse(BaseModel):
    items: list[ListingOut] = Field(default_factory=list)


class CreateListingRequest(BaseModel):
    kind: ListingKind
    title: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=1, max_length=10_000)
    price: float = Field(ge=0)
    location_id: UUID
    category_id: UUID
    status: ListingStatus = ListingStatus.draft  # owner can create draft or pending


class UpdateListingRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=10_000)
    price: float | None = Field(default=None, ge=0)
    location_id: UUID | None = None
    category_id: UUID | None = None
    status: ListingStatus | None = None  # allow draft->pending


class UploadListingPhotoResponse(BaseModel):
    photo: ListingPhotoOut

