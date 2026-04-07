from __future__ import annotations

from uuid import UUID

import uuid

from fastapi import APIRouter, File, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.modules.auth.deps import CurrentUser, OptionalCurrentUser
from app.modules.listings.models import Listing, ListingPhoto, ListingStatus
from app.modules.listings.schemas import (
    CreateListingRequest,
    ListingListResponse,
    ListingOut,
    ListingPhotoOut,
    UploadListingPhotoResponse,
    UpdateListingRequest,
)
from app.modules.listings.service import (
    can_owner_edit,
    ensure_owner,
    get_listing_for_view,
    increment_views,
    owner_allowed_status_transition,
)
from app.modules.listings.models import ListingKind

from app.core.config import settings
from app.storage.service import get_storage
from app.modules.search.indexer import delete_listing as ts_delete_listing, upsert_listing as ts_upsert_listing
from app.modules.users.models import User
from app.modules.ranking.service import base_boost_score

router = APIRouter(prefix="/listings", tags=["listings"])


def _photo_out(p: ListingPhoto) -> ListingPhotoOut:
    storage = get_storage()
    return ListingPhotoOut(
        id=p.id,
        key=p.key,
        url=storage.public_url(key=p.key),
        content_type=p.content_type,
        sort_order=int(p.sort_order),
        created_at=p.created_at,
    )


def _listing_out(l: Listing) -> ListingOut:
    return ListingOut(
        id=l.id,
        kind=l.kind,
        status=l.status,
        title=l.title,
        description=l.description,
        price=float(l.price),
        location_id=l.location_id,
        category_id=l.category_id,
        owner_id=l.owner_id,
        published_at=l.published_at,
        views_count=int(l.views_count),
        favorites_count=int(l.favorites_count),
        boost_score=float(l.boost_score),
        photos=[_photo_out(p) for p in (l.photos or [])],
        created_at=l.created_at,
        updated_at=l.updated_at,
    )


class InvalidStatusTransitionError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="invalid_status_transition",
            message="Invalid status transition",
            status_code=400,
        )


@router.post("", response_model=ListingOut, status_code=201)
async def create_listing(payload: CreateListingRequest, db: DbSession, user: CurrentUser) -> ListingOut:
    if payload.status not in (ListingStatus.draft, ListingStatus.pending):
        raise InvalidStatusTransitionError()

    listing = Listing(
        owner_id=user.id,
        kind=payload.kind,
        status=payload.status,
        title=payload.title,
        description=payload.description,
        price=payload.price,
        location_id=payload.location_id,
        category_id=payload.category_id,
        published_at=None,
    )
    # initialize boost_score server-side (query-independent)
    listing.boost_score = base_boost_score(listing=listing, owner=user).score
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return _listing_out(listing)


@router.get("", response_model=ListingListResponse)
async def list_public_active_listings(
    db: DbSession,
    kind: ListingKind | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    location_id: UUID | None = Query(default=None),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    q: str | None = Query(default=None, max_length=100, description="Search query placeholder"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> ListingListResponse:
    stmt = (
        select(Listing)
        .where(Listing.status == ListingStatus.active)
        .options(selectinload(Listing.photos))
        .order_by(Listing.published_at.desc().nullslast(), Listing.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if kind is not None:
        stmt = stmt.where(Listing.kind == kind)
    if category_id is not None:
        stmt = stmt.where(Listing.category_id == category_id)
    if location_id is not None:
        stmt = stmt.where(Listing.location_id == location_id)
    if min_price is not None:
        stmt = stmt.where(Listing.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Listing.price <= max_price)
    # q placeholder: not applied yet (Typesense later)
    _ = q

    rows = (await db.scalars(stmt)).all()
    return ListingListResponse(items=[_listing_out(x) for x in rows])


@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing_by_id(
    listing_id: UUID,
    db: DbSession,
    viewer: OptionalCurrentUser,
) -> ListingOut:
    viewer_user_id: UUID | None = viewer.id if viewer is not None else None

    listing = await get_listing_for_view(db, listing_id=listing_id, viewer_user_id=viewer_user_id)

    # only increment for public active views
    if listing.status == ListingStatus.active:
        await increment_views(db, listing_id=listing.id)
        await db.commit()
        await db.refresh(listing)
    return _listing_out(listing)


@router.patch("/{listing_id}", response_model=ListingOut)
async def update_own_listing(
    listing_id: UUID, payload: UpdateListingRequest, db: DbSession, user: CurrentUser
) -> ListingOut:
    listing = await db.scalar(
        select(Listing).where(Listing.id == listing_id).options(selectinload(Listing.photos))
    )
    if listing is None:
        raise NotFoundError("Listing not found")
    await ensure_owner(listing, user_id=user.id)

    if not can_owner_edit(listing.status):
        raise ForbiddenError("Listing cannot be edited in its current status")

    if payload.status is not None:
        if not owner_allowed_status_transition(from_status=listing.status, to_status=payload.status):
            raise InvalidStatusTransitionError()
        listing.status = payload.status

    if payload.title is not None:
        listing.title = payload.title
    if payload.description is not None:
        listing.description = payload.description
    if payload.price is not None:
        listing.price = payload.price
    if payload.location_id is not None:
        listing.location_id = payload.location_id
    if payload.category_id is not None:
        listing.category_id = payload.category_id

    await db.commit()
    await db.refresh(listing)

    # recompute base boost score when listing changes (cheap MVP approach)
    owner = await db.get(User, listing.owner_id)
    if owner is not None:
        listing.boost_score = base_boost_score(listing=listing, owner=owner).score
        await db.commit()
        await db.refresh(listing)

    # keep Typesense in sync (active only)
    if listing.status == ListingStatus.active:
        await ts_upsert_listing(db, listing_id=listing.id)
    if listing.status in (ListingStatus.archived, ListingStatus.rejected):
        await ts_delete_listing(listing_id=listing.id)
    return _listing_out(listing)


@router.post("/{listing_id}/archive", response_model=ListingOut)
async def archive_own_listing(listing_id: UUID, db: DbSession, user: CurrentUser) -> ListingOut:
    listing = await db.scalar(
        select(Listing).where(Listing.id == listing_id).options(selectinload(Listing.photos))
    )
    if listing is None:
        raise NotFoundError("Listing not found")
    await ensure_owner(listing, user_id=user.id)

    if not owner_allowed_status_transition(from_status=listing.status, to_status=ListingStatus.archived):
        raise InvalidStatusTransitionError()

    listing.status = ListingStatus.archived
    await db.commit()
    await db.refresh(listing)
    await ts_delete_listing(listing_id=listing.id)
    return _listing_out(listing)


@router.post("/{listing_id}/submit", response_model=ListingOut)
async def submit_for_moderation(listing_id: UUID, db: DbSession, user: CurrentUser) -> ListingOut:
    listing = await db.scalar(
        select(Listing).where(Listing.id == listing_id).options(selectinload(Listing.photos))
    )
    if listing is None:
        raise NotFoundError("Listing not found")
    await ensure_owner(listing, user_id=user.id)

    if not owner_allowed_status_transition(from_status=listing.status, to_status=ListingStatus.pending):
        raise InvalidStatusTransitionError()

    listing.status = ListingStatus.pending
    await db.commit()
    await db.refresh(listing)
    return _listing_out(listing)


class InvalidUploadError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(code="invalid_upload", message=message, status_code=400)


@router.post("/{listing_id}/photos", response_model=UploadListingPhotoResponse, status_code=201)
async def upload_listing_photo(
    listing_id: UUID,
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    order_index: int = Query(default=0, ge=0, le=50),
) -> UploadListingPhotoResponse:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise NotFoundError("Listing not found")
    await ensure_owner(listing, user_id=user.id)

    content_type = (file.content_type or "").lower()
    if content_type not in set(settings.upload_allowed_image_types):
        raise InvalidUploadError("Unsupported image type")

    data = await file.read()
    if not data:
        raise InvalidUploadError("Empty file")
    if len(data) > settings.upload_max_bytes:
        raise InvalidUploadError("File too large")

    ext = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }.get(content_type, "bin")

    key = f"listings/{listing_id}/{uuid.uuid4().hex}.{ext}"
    storage = get_storage()
    stored = await storage.put_bytes(key=key, data=data, content_type=content_type)

    photo = ListingPhoto(
        listing_id=listing_id,
        key=stored.key,
        content_type=stored.content_type,
        sort_order=order_index,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return UploadListingPhotoResponse(photo=_photo_out(photo))


@router.delete("/{listing_id}/photos/{photo_id}", response_model=dict)
async def delete_listing_photo(
    listing_id: UUID,
    photo_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    listing = await db.scalar(select(Listing).where(Listing.id == listing_id))
    if listing is None:
        raise NotFoundError("Listing not found")
    await ensure_owner(listing, user_id=user.id)

    photo = await db.scalar(
        select(ListingPhoto).where(ListingPhoto.id == photo_id, ListingPhoto.listing_id == listing_id)
    )
    if photo is None:
        raise NotFoundError("Photo not found")

    storage = get_storage()
    await storage.delete(key=photo.key)
    await db.delete(photo)
    await db.commit()
    return {"status": "deleted"}

