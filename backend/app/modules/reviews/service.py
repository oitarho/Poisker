from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, NotFoundError
from app.modules.listings.models import Listing
from app.modules.reviews.models import Review
from app.modules.users.models import User


class SelfReviewError(AppError):
    def __init__(self) -> None:
        super().__init__(code="self_review", message="You cannot review yourself", status_code=400)


class DuplicateReviewError(AppError):
    def __init__(self) -> None:
        super().__init__(code="duplicate_review", message="Duplicate review", status_code=409)


async def recompute_user_rating(db: AsyncSession, *, user_id) -> None:
    row = await db.execute(
        select(func.count(Review.id), func.avg(Review.rating)).where(Review.target_user_id == user_id)
    )
    count, avg = row.one()
    u = await db.get(User, user_id)
    if u is None:
        raise NotFoundError("User not found")
    u.reviews_count = int(count or 0)
    u.rating = float(avg or 0.0)


async def create_review(
    db: AsyncSession,
    *,
    reviewer_id,
    target_user_id,
    listing_id,
    rating: int,
    text: str | None,
) -> Review:
    if reviewer_id == target_user_id:
        raise SelfReviewError()

    # If listing is provided, ensure the target user is the listing owner (prevents arbitrary targeting).
    if listing_id is not None:
        listing = await db.get(Listing, listing_id)
        if listing is None:
            raise NotFoundError("Listing not found")
        if listing.owner_id != target_user_id:
            raise AppError(
                code="invalid_review_target",
                message="Target user must be the listing owner",
                status_code=400,
            )

    review = Review(
        reviewer_id=reviewer_id,
        target_user_id=target_user_id,
        listing_id=listing_id,
        rating=rating,
        text=text,
    )
    db.add(review)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise DuplicateReviewError()

    await recompute_user_rating(db, user_id=target_user_id)
    return review

