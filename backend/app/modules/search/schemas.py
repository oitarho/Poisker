from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.listings.schemas import ListingOut


class SearchResponse(BaseModel):
    items: list[ListingOut] = Field(default_factory=list)
    found: int = 0
    debug: dict | None = None
