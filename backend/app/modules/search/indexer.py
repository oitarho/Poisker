from __future__ import annotations

from datetime import datetime, timezone

import anyio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only

from app.core.config import settings
from app.integrations.typesense import get_typesense_client
from app.modules.listings.models import Listing, ListingStatus
from app.modules.search.typesense_schema import listings_collection_schema


def _ts(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


async def ensure_listings_collection() -> None:
    client = get_typesense_client()
    name = settings.typesense_listings_collection

    def _ensure() -> None:
        try:
            client.collections[name].retrieve()
        except Exception:
            client.collections.create(listings_collection_schema())

    await anyio.to_thread.run_sync(_ensure)


def listing_to_document(l: Listing) -> dict:
    return {
        "id": str(l.id),
        "title": l.title,
        "description": l.description,
        "kind": l.kind.value,
        "status": l.status.value,
        "category_id": str(l.category_id),
        "location_id": str(l.location_id),
        "owner_id": str(l.owner_id),
        "price": float(l.price),
        "created_at": _ts(l.created_at) or 0,
        "published_at": _ts(l.published_at),
        "views_count": int(l.views_count),
        "favorites_count": int(l.favorites_count),
        "boost_score": float(l.boost_score),
    }


async def upsert_listing(db: AsyncSession, *, listing_id) -> None:
    listing = await db.get(Listing, listing_id)
    if listing is None:
        return
    if listing.status != ListingStatus.active:
        # only active listings are indexed
        await delete_listing(listing_id=listing_id)
        return

    await ensure_listings_collection()
    doc = listing_to_document(listing)
    client = get_typesense_client()
    name = settings.typesense_listings_collection

    def _upsert() -> None:
        client.collections[name].documents.upsert(doc)

    await anyio.to_thread.run_sync(_upsert)


async def delete_listing(*, listing_id) -> None:
    client = get_typesense_client()
    name = settings.typesense_listings_collection

    def _delete() -> None:
        try:
            client.collections[name].documents[str(listing_id)].delete()
        except Exception:
            return

    await anyio.to_thread.run_sync(_delete)


async def reindex_all_active(db: AsyncSession) -> int:
    await ensure_listings_collection()
    client = get_typesense_client()
    name = settings.typesense_listings_collection

    ids = (
        await db.scalars(select(Listing.id).where(Listing.status == ListingStatus.active))
    ).all()

    async def _upsert_one(lid):
        await upsert_listing(db, listing_id=lid)

    for lid in ids:
        await _upsert_one(lid)
    return len(ids)

