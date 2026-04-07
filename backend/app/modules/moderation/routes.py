from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.modules.listings.models import Listing, ListingStatus
from app.modules.listings.routes import _listing_out
from app.modules.moderation.deps import Admin
from app.modules.moderation.schemas import ModerationActionResponse, RejectRequest
from app.modules.moderation.service import approve_listing, archive_active_listing, reject_listing

router = APIRouter(prefix="/admin/listings", tags=["admin", "moderation"])


@router.get("/pending", response_model=dict)
async def list_pending_listings(db: DbSession, _: Admin) -> dict:
    rows = (
        await db.scalars(
            select(Listing)
            .where(Listing.status == ListingStatus.pending)
            .options(selectinload(Listing.photos))
            .order_by(Listing.created_at.asc())
            .limit(100)
        )
    ).all()
    return {"items": [_listing_out(x).model_dump() for x in rows]}


@router.post("/{listing_id}/approve", response_model=ModerationActionResponse)
async def approve(listing_id: UUID, db: DbSession, _: Admin) -> ModerationActionResponse:
    listing = await db.get(Listing, listing_id)
    if listing is None:
        # service already raises, but we need from_status for response; keep it simple:
        from app.core.errors import NotFoundError

        raise NotFoundError("Listing not found")
    from_status = listing.status
    updated = await approve_listing(db, listing_id=listing_id, actor_admin_user_id=None)
    return ModerationActionResponse(
        listing_id=updated.id,
        from_status=from_status,
        to_status=updated.status,
        reason=None,
        updated_at=updated.updated_at,
    )


@router.post("/{listing_id}/reject", response_model=ModerationActionResponse)
async def reject(listing_id: UUID, payload: RejectRequest, db: DbSession, _: Admin) -> ModerationActionResponse:
    listing = await db.get(Listing, listing_id)
    if listing is None:
        from app.core.errors import NotFoundError

        raise NotFoundError("Listing not found")
    from_status = listing.status
    updated = await reject_listing(
        db, listing_id=listing_id, reason=payload.reason, actor_admin_user_id=None
    )
    return ModerationActionResponse(
        listing_id=updated.id,
        from_status=from_status,
        to_status=updated.status,
        reason=payload.reason,
        updated_at=updated.updated_at,
    )


@router.post("/{listing_id}/archive", response_model=ModerationActionResponse)
async def archive(listing_id: UUID, db: DbSession, _: Admin) -> ModerationActionResponse:
    listing = await db.get(Listing, listing_id)
    if listing is None:
        from app.core.errors import NotFoundError

        raise NotFoundError("Listing not found")
    from_status = listing.status
    updated = await archive_active_listing(db, listing_id=listing_id, reason=None, actor_admin_user_id=None)
    return ModerationActionResponse(
        listing_id=updated.id,
        from_status=from_status,
        to_status=updated.status,
        reason=None,
        updated_at=updated.updated_at,
    )

