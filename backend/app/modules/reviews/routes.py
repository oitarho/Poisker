from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DbSession
from app.modules.auth.deps import CurrentUser
from app.modules.reviews.models import Review
from app.modules.reviews.schemas import CreateReviewRequest, ReviewListResponse, ReviewOut
from app.modules.reviews.service import create_review

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _out(r: Review) -> ReviewOut:
    return ReviewOut(
        id=r.id,
        reviewer_id=r.reviewer_id,
        target_user_id=r.target_user_id,
        listing_id=r.listing_id,
        rating=int(r.rating),
        text=r.text,
        created_at=r.created_at,
    )


@router.post("", response_model=ReviewOut, status_code=201)
async def leave_review(payload: CreateReviewRequest, db: DbSession, user: CurrentUser) -> ReviewOut:
    review = await create_review(
        db,
        reviewer_id=user.id,
        target_user_id=payload.target_user_id,
        listing_id=payload.listing_id,
        rating=payload.rating,
        text=payload.text,
    )
    await db.commit()
    await db.refresh(review)
    return _out(review)


@router.get("/users/{user_id}", response_model=ReviewListResponse)
async def list_reviews_for_user(
    user_id: UUID,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> ReviewListResponse:
    stmt = (
        select(Review)
        .where(Review.target_user_id == user_id)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.scalars(stmt)).all()
    return ReviewListResponse(items=[_out(x) for x in rows])

