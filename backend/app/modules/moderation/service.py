from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError
from app.modules.listings.models import Listing, ListingStatus
from app.modules.moderation.models import ModerationEntityType, ModerationLog
from app.modules.search.indexer import delete_listing as ts_delete_listing, upsert_listing as ts_upsert_listing


def _now() -> datetime:
    return datetime.now(timezone.utc)


class InvalidModerationTransitionError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="invalid_transition",
            message="Invalid moderation transition",
            status_code=400,
        )


async def _log_status_change(
    db: AsyncSession,
    *,
    actor_admin_user_id: UUID | None,
    listing: Listing,
    from_status: ListingStatus,
    to_status: ListingStatus,
    reason: str | None,
) -> None:
    db.add(
        ModerationLog(
            actor_admin_user_id=actor_admin_user_id,
            entity_type=ModerationEntityType.listing,
            entity_id=listing.id,
            action="listing_status_change",
            reason=reason,
            extra={"from": from_status.value, "to": to_status.value},
            listing_id=listing.id,
        )
    )


async def approve_listing(db: AsyncSession, *, listing_id: UUID, actor_admin_user_id: UUID | None = None) -> Listing:
    listing = await db.get(Listing, listing_id)
    if listing is None:
        raise NotFoundError("Listing not found")
    if listing.status != ListingStatus.pending:
        raise InvalidModerationTransitionError()

    from_status = listing.status
    listing.status = ListingStatus.active
    listing.published_at = listing.published_at or _now()

    await _log_status_change(
        db, actor_admin_user_id=actor_admin_user_id, listing=listing, from_status=from_status, to_status=listing.status, reason=None
    )
    await db.commit()
    await db.refresh(listing)

    await ts_upsert_listing(db, listing_id=listing.id)
    return listing


async def reject_listing(
    db: AsyncSession,
    *,
    listing_id: UUID,
    reason: str,
    actor_admin_user_id: UUID | None = None,
) -> Listing:
    listing = await db.get(Listing, listing_id)
    if listing is None:
        raise NotFoundError("Listing not found")
    if listing.status != ListingStatus.pending:
        raise InvalidModerationTransitionError()

    from_status = listing.status
    listing.status = ListingStatus.rejected
    await _log_status_change(
        db,
        actor_admin_user_id=actor_admin_user_id,
        listing=listing,
        from_status=from_status,
        to_status=listing.status,
        reason=reason,
    )
    await db.commit()
    await db.refresh(listing)
    await ts_delete_listing(listing_id=listing.id)
    return listing


async def archive_active_listing(
    db: AsyncSession,
    *,
    listing_id: UUID,
    reason: str | None = None,
    actor_admin_user_id: UUID | None = None,
) -> Listing:
    listing = await db.get(Listing, listing_id)
    if listing is None:
        raise NotFoundError("Listing not found")
    if listing.status != ListingStatus.active:
        raise InvalidModerationTransitionError()

    from_status = listing.status
    listing.status = ListingStatus.archived
    await _log_status_change(
        db,
        actor_admin_user_id=actor_admin_user_id,
        listing=listing,
        from_status=from_status,
        to_status=listing.status,
        reason=reason,
    )
    await db.commit()
    await db.refresh(listing)
    await ts_delete_listing(listing_id=listing.id)
    return listing

