from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.listings.schemas import ListingOut


class FavoriteStatusResponse(BaseModel):
    favorited: bool


class FavoritesListResponse(BaseModel):
    items: list[ListingOut] = Field(default_factory=list)

