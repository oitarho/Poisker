from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError, NotFoundError
from app.modules.listings.models import Listing, ListingStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_listing_for_view(
    db: AsyncSession, *, listing_id: UUID, viewer_user_id: UUID | None
) -> Listing:
    listing = await db.scalar(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(selectinload(Listing.photos))
    )
    if listing is None:
        raise NotFoundError("Listing not found")

    if listing.status == ListingStatus.active:
        return listing

    # non-active listings are visible only to owner (admin later)
    if viewer_user_id is None or listing.owner_id != viewer_user_id:
        raise NotFoundError("Listing not found")
    return listing


async def ensure_owner(listing: Listing, *, user_id: UUID) -> None:
    if listing.owner_id != user_id:
        raise ForbiddenError("You do not own this listing")


async def increment_views(db: AsyncSession, *, listing_id: UUID) -> None:
    await db.execute(
        update(Listing).where(Listing.id == listing_id).values(views_count=Listing.views_count + 1)
    )


def can_owner_edit(status: ListingStatus) -> bool:
    return status in (ListingStatus.draft, ListingStatus.pending, ListingStatus.rejected, ListingStatus.active)


def owner_allowed_status_transition(*, from_status: ListingStatus, to_status: ListingStatus) -> bool:
    if to_status == from_status:
        return True
    if from_status == ListingStatus.draft and to_status == ListingStatus.pending:
        return True
    if to_status == ListingStatus.archived and from_status in (
        ListingStatus.draft,
        ListingStatus.pending,
        ListingStatus.active,
        ListingStatus.rejected,
    ):
        return True
    # owner cannot self-activate or self-reject
    return False

