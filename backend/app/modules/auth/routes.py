from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from app.api.deps import DbSession
from app.modules.auth.deps import CurrentUser, OptionalCurrentUser
from app.modules.auth.email_auth import (
    PASSWORD_RESET_OK_MESSAGE,
    confirm_email_verification,
    confirm_password_reset,
    request_password_reset,
    send_verification_email_flow,
)
from app.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetConfirmResult,
    PasswordResetRequestBody,
    PasswordResetRequestResult,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserMe,
    VerifyEmailConfirmRequest,
    VerifyEmailConfirmResult,
    VerifyEmailRequestBody,
    VerifyEmailRequestResult,
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
        email_verified_at=u.email_verified_at,
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


@router.post("/verify-email/request", response_model=VerifyEmailRequestResult)
async def verify_email_request(
    db: DbSession,
    body: VerifyEmailRequestBody = Body(default_factory=VerifyEmailRequestBody),
    user: OptionalCurrentUser = None,
) -> VerifyEmailRequestResult:
    if user is not None:
        target_email = user.email
    else:
        if not body.email:
            raise HTTPException(status_code=422, detail="email is required when not authenticated")
        target_email = str(body.email)

    status = await send_verification_email_flow(db, email=target_email)
    if status == "already_verified":
        return VerifyEmailRequestResult(
            status="already_verified",
            message="Email is already verified.",
        )
    return VerifyEmailRequestResult(
        status="sent",
        message="Verification code sent to your email.",
    )


@router.post("/verify-email/confirm", response_model=VerifyEmailConfirmResult)
async def verify_email_confirm(db: DbSession, payload: VerifyEmailConfirmRequest) -> VerifyEmailConfirmResult:
    status = await confirm_email_verification(db, email=str(payload.email), code=payload.code)
    if status == "already_verified":
        return VerifyEmailConfirmResult(
            status="already_verified",
            message="Email was already verified.",
        )
    return VerifyEmailConfirmResult(
        status="verified",
        message="Email verified successfully.",
    )


@router.post("/password-reset/request", response_model=PasswordResetRequestResult)
async def password_reset_request_ep(db: DbSession, payload: PasswordResetRequestBody) -> PasswordResetRequestResult:
    await request_password_reset(db, email=str(payload.email))
    return PasswordResetRequestResult(message=PASSWORD_RESET_OK_MESSAGE)


@router.post("/password-reset/confirm", response_model=PasswordResetConfirmResult)
async def password_reset_confirm_ep(
    db: DbSession, payload: PasswordResetConfirmRequest
) -> PasswordResetConfirmResult:
    await confirm_password_reset(
        db,
        email=str(payload.email),
        code=payload.code,
        new_password=payload.new_password,
    )
    return PasswordResetConfirmResult()
