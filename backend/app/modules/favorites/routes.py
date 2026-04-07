from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.core.errors import AppError, NotFoundError
from app.modules.auth.deps import CurrentUser
from app.modules.favorites.models import Favorite
from app.modules.favorites.schemas import FavoriteStatusResponse, FavoritesListResponse
from app.modules.listings.models import Listing, ListingStatus
from app.modules.listings.routes import _listing_out

router = APIRouter(prefix="/favorites", tags=["favorites"])


class AlreadyFavoritedError(AppError):
    def __init__(self) -> None:
        super().__init__(code="already_favorited", message="Already in favorites", status_code=409)


class NotFavoritedError(AppError):
    def __init__(self) -> None:
        super().__init__(code="not_favorited", message="Not in favorites", status_code=404)


async def _can_favorite(listing: Listing, *, user_id: UUID) -> bool:
    return listing.status == ListingStatus.active or listing.owner_id == user_id


@router.post("/{listing_id}", response_model=FavoriteStatusResponse, status_code=201)
async def add_favorite(listing_id: UUID, db: DbSession, user: CurrentUser) -> FavoriteStatusResponse:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise NotFoundError("Listing not found")
    if not await _can_favorite(listing, user_id=user.id):
        # don't leak non-public listing existence
        raise NotFoundError("Listing not found")

    fav = Favorite(user_id=user.id, listing_id=listing_id)
    db.add(fav)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise AlreadyFavoritedError()

    await db.execute(
        update(Listing)
        .where(Listing.id == listing_id)
        .values(favorites_count=Listing.favorites_count + 1)
    )
    await db.commit()
    return FavoriteStatusResponse(favorited=True)


@router.delete("/{listing_id}", response_model=FavoriteStatusResponse)
async def remove_favorite(listing_id: UUID, db: DbSession, user: CurrentUser) -> FavoriteStatusResponse:
    res = await db.execute(
        delete(Favorite)
        .where(Favorite.user_id == user.id, Favorite.listing_id == listing_id)
        .returning(Favorite.id)
    )
    deleted_id = res.scalar_one_or_none()
    if deleted_id is None:
        raise NotFavoritedError()

    await db.execute(
        update(Listing)
        .where(Listing.id == listing_id, Listing.favorites_count > 0)
        .values(favorites_count=Listing.favorites_count - 1)
    )
    await db.commit()
    return FavoriteStatusResponse(favorited=False)


@router.get("", response_model=FavoritesListResponse)
async def list_my_favorites(
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> FavoritesListResponse:
    stmt = (
        select(Listing)
        .join(Favorite, Favorite.listing_id == Listing.id)
        .where(Favorite.user_id == user.id)
        .options(selectinload(Listing.photos))
        .order_by(Favorite.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.scalars(stmt)).all()
    return FavoritesListResponse(items=[_listing_out(x) for x in rows])

