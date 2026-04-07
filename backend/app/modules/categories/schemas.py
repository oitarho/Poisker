from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.categories.models import CategoryScope


class CategoryOut(BaseModel):
    id: UUID
    name: str
    slug: str
    scope: CategoryScope
    parent_id: UUID | None
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    items: list[CategoryOut] = Field(default_factory=list)

