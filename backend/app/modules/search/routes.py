from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload

from app.api.deps import DbSession
from app.core.config import settings
from app.integrations.typesense import get_typesense_client
from app.modules.listings.models import Listing, ListingStatus
from app.modules.listings.schemas import ListingOut
from app.modules.search.indexer import ensure_listings_collection
from app.modules.search.schemas import SearchResponse
from app.modules.ranking.service import score_listing

router = APIRouter(prefix="/search", tags=["search"])


def _build_filter(
    *,
    kind: str | None,
    category_id: UUID | None,
    location_id: UUID | None,
    min_price: float | None,
    max_price: float | None,
) -> str:
    parts: list[str] = ["status:=active"]
    if kind:
        parts.append(f"kind:={kind}")
    if category_id:
        parts.append(f"category_id:={category_id}")
    if location_id:
        parts.append(f"location_id:={location_id}")
    if min_price is not None and max_price is not None:
        parts.append(f"price:>={min_price} && price:<={max_price}")
    elif min_price is not None:
        parts.append(f"price:>={min_price}")
    elif max_price is not None:
        parts.append(f"price:<={max_price}")
    return " && ".join(parts)


@router.get("", response_model=SearchResponse)
async def search_listings(
    db: DbSession,
    q: str = Query(default="*", max_length=100),
    kind: str | None = Query(default=None, description="product|service"),
    category_id: UUID | None = None,
    location_id: UUID | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    sort: str | None = Query(default=None, description="Ranking/sorting placeholder"),
    debug: bool = Query(default=False, description="Dev-only ranking breakdown"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    await ensure_listings_collection()
    client = get_typesense_client()

    filter_by = _build_filter(
        kind=kind,
        category_id=category_id,
        location_id=location_id,
        min_price=min_price,
        max_price=max_price,
    )
    _ = sort  # placeholder (ranking module later)

    res = client.collections[settings.typesense_listings_collection].documents.search(
        {
            "q": q or "*",
            "query_by": "title,description",
            "filter_by": filter_by,
            "per_page": limit,
            "page": (offset // limit) + 1,
            "sort_by": "boost_score:desc, favorites_count:desc, published_at:desc",
        }
    )

    hits = res.get("hits", []) or []
    found = int(res.get("found", 0) or 0)
    ids: list[UUID] = []
    text_match_by_id: dict[UUID, int] = {}
    for h in hits:
        doc = h.get("document") or {}
        if not doc.get("id"):
            continue
        lid = UUID(doc["id"])
        ids.append(lid)
        tm = h.get("text_match")
        if isinstance(tm, int):
            text_match_by_id[lid] = tm
    if not ids:
        return SearchResponse(items=[], found=found, debug=None)

    rows = (
        await db.scalars(
            select(Listing)
            .where(Listing.id.in_(ids), Listing.status == ListingStatus.active)
            .options(selectinload(Listing.photos), joinedload(Listing.owner))
        )
    ).all()
    by_id = {r.id: r for r in rows}

    # hydrate in Typesense order, but optionally rerank server-side
    from app.modules.listings.routes import _listing_out  # local reuse for MVP

    max_tm = max(text_match_by_id.values(), default=0) or 1

    scored: list[tuple[UUID, float, dict[str, float] | None]] = []
    for lid in ids:
        l = by_id.get(lid)
        if not l or l.owner is None:
            continue
        tm = float(text_match_by_id.get(lid, 0)) / float(max_tm)
        ranked = score_listing(listing=l, owner=l.owner, text_relevance=tm)
        scored.append((lid, ranked.score, ranked.breakdown if (debug and settings.env == "local") else None))

    # sort placeholder: default is ranked; can be overridden later
    _ = sort
    scored.sort(key=lambda x: x[1], reverse=True)

    items: list[ListingOut] = [_listing_out(by_id[lid]) for (lid, _s, _b) in scored if lid in by_id]

    debug_payload = None
    if debug and settings.env == "local":
        debug_payload = {
            "max_text_match": max_tm,
            "items": [
                {"listing_id": str(lid), "score": s, "breakdown": b} for (lid, s, b) in scored
            ],
        }

    return SearchResponse(items=items, found=found, debug=debug_payload)

