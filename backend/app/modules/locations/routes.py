from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.errors import NotFoundError
from app.modules.locations.models import Location
from app.modules.locations.schemas import LocationListResponse, LocationOut

router = APIRouter(prefix="/locations", tags=["locations"])


def _out(l: Location) -> LocationOut:
    return LocationOut(
        id=l.id,
        name=l.name,
        type=l.type,
        parent_id=l.parent_id,
        latitude=float(l.latitude) if l.latitude is not None else None,
        longitude=float(l.longitude) if l.longitude is not None else None,
        created_at=l.created_at,
        updated_at=l.updated_at,
    )


@router.get("/roots", response_model=LocationListResponse)
async def list_roots(db: DbSession) -> LocationListResponse:
    rows = (await db.scalars(select(Location).where(Location.parent_id.is_(None)).order_by(Location.name))).all()
    return LocationListResponse(items=[_out(x) for x in rows])


@router.get("/{parent_id}/children", response_model=LocationListResponse)
async def list_children(parent_id: UUID, db: DbSession) -> LocationListResponse:
    rows = (
        await db.scalars(select(Location).where(Location.parent_id == parent_id).order_by(Location.name))
    ).all()
    return LocationListResponse(items=[_out(x) for x in rows])


@router.get("/search", response_model=LocationListResponse)
async def search_locations(
    db: DbSession,
    q: str = Query(min_length=1, max_length=50),
) -> LocationListResponse:
    # Postgres ILIKE for simple name search; ready to be replaced by trigram/geo later.
    pattern = f"%{q.strip()}%"
    rows = (
        await db.scalars(select(Location).where(Location.name.ilike(pattern)).order_by(Location.name).limit(50))
    ).all()
    return LocationListResponse(items=[_out(x) for x in rows])


@router.get("/{location_id}", response_model=LocationOut)
async def get_location(location_id: UUID, db: DbSession) -> LocationOut:
    row = await db.get(Location, location_id)
    if row is None:
        raise NotFoundError("Location not found")
    return _out(row)

