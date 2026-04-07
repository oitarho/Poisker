from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.core.errors import NotFoundError
from app.modules.auth.deps import CurrentUser
from app.modules.users.models import User
from app.modules.users.public_schemas import PublicUserProfile
from app.modules.users.schemas import UpdateMyProfileRequest, UserProfile

router = APIRouter(prefix="/users", tags=["users"])


def _profile(u) -> UserProfile:
    return UserProfile(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        phone_number=u.phone_number,
        is_email_verified=u.is_email_verified,
        email_verified_at=u.email_verified_at,
        is_phone_verified=u.is_phone_verified,
        rating=float(u.rating),
        reviews_count=int(u.reviews_count),
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


@router.get("/me", response_model=UserProfile)
async def get_my_profile(user: CurrentUser) -> UserProfile:
    return _profile(user)


@router.patch("/me", response_model=UserProfile)
async def update_my_profile(
    payload: UpdateMyProfileRequest,
    db: DbSession,
    user: CurrentUser,
) -> UserProfile:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    # allow explicit clearing by sending "" (validator converts to None)
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number
    if payload.clear_phone_number:
        user.phone_number = None

    await db.commit()
    await db.refresh(user)
    return _profile(user)


from uuid import UUID


@router.get("/{user_id}/public", response_model=PublicUserProfile)
async def get_public_user_profile(user_id: UUID, db: DbSession) -> PublicUserProfile:
    u = await db.get(User, user_id)
    if u is None:
        raise NotFoundError("User not found")
    return PublicUserProfile(
        id=u.id,
        full_name=u.full_name,
        is_phone_verified=u.is_phone_verified,
        rating=float(u.rating),
        reviews_count=int(u.reviews_count),
    )

