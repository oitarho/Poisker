from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSession
from app.modules.auth.deps import CurrentUser
from app.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserMe,
)
from app.modules.auth.service import login_user, refresh_tokens, register_user
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_me(u: User) -> UserMe:
    return UserMe(
        id=u.id,
        email=u.email,
        full_name=u.full_name,
        phone_number=u.phone_number,
        is_email_verified=u.is_email_verified,
        is_phone_verified=u.is_phone_verified,
        rating=float(u.rating),
        reviews_count=int(u.reviews_count),
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegisterRequest, db: DbSession) -> AuthResponse:
    user, access, refresh = await register_user(
        db,
        email=str(payload.email),
        password=payload.password,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
    )
    return AuthResponse(tokens=TokenPair(access_token=access, refresh_token=refresh), user=_user_me(user))


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: DbSession) -> AuthResponse:
    user, access, refresh = await login_user(db, email=str(payload.email), password=payload.password)
    return AuthResponse(tokens=TokenPair(access_token=access, refresh_token=refresh), user=_user_me(user))


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: DbSession) -> TokenPair:
    _user, access, refresh_token = await refresh_tokens(db, refresh_token=payload.refresh_token)
    return TokenPair(access_token=access, refresh_token=refresh_token)


@router.get("/me", response_model=UserMe)
async def me(user: CurrentUser) -> UserMe:
    return _user_me(user)

