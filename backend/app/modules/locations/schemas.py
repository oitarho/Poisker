from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.locations.models import LocationType


class LocationOut(BaseModel):
    id: UUID
    name: str
    type: LocationType
    parent_id: UUID | None
    latitude: float | None
    longitude: float | None
    created_at: datetime
    updated_at: datetime


class LocationListResponse(BaseModel):
    items: list[LocationOut] = Field(default_factory=list)

