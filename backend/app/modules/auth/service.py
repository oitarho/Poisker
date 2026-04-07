from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, UnauthorizedError
from app.core.security import hash_password, verify_password, decode_token, is_jwt_error
from app.modules.auth.tokens import issue_token_pair, new_jti, refresh_expires_at
from app.modules.users.models import RefreshToken, User


class EmailAlreadyTakenError(AppError):
    def __init__(self) -> None:
        super().__init__(code="email_taken", message="Email is already registered", status_code=409)


class InvalidCredentialsError(AppError):
    def __init__(self) -> None:
        super().__init__(code="invalid_credentials", message="Invalid email or password", status_code=401)


class InvalidRefreshTokenError(AppError):
    def __init__(self) -> None:
        super().__init__(code="invalid_refresh_token", message="Invalid refresh token", status_code=401)


async def register_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str | None = None,
    phone_number: str | None = None,
) -> tuple[User, str, str]:
    user = User(
        email=email.lower().strip(),
        password_hash=hash_password(password),
        full_name=full_name,
        phone_number=phone_number,
        is_email_verified=False,
        is_phone_verified=False,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise EmailAlreadyTakenError()

    jti = new_jti()
    rt = RefreshToken(user_id=user.id, jti=jti, revoked=False, expires_at=refresh_expires_at())
    db.add(rt)
    await db.commit()

    access, refresh = issue_token_pair(user_id=str(user.id), refresh_jti=jti)
    return user, access, refresh


async def login_user(db: AsyncSession, *, email: str, password: str) -> tuple[User, str, str]:
    normalized = email.lower().strip()
    user = await db.scalar(select(User).where(User.email == normalized))
    if user is None:
        raise InvalidCredentialsError()
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError()

    user.last_login_at = datetime.now(timezone.utc)

    jti = new_jti()
    rt = RefreshToken(user_id=user.id, jti=jti, revoked=False, expires_at=refresh_expires_at())
    db.add(rt)
    await db.commit()

    access, refresh = issue_token_pair(user_id=str(user.id), refresh_jti=jti)
    return user, access, refresh


async def refresh_tokens(db: AsyncSession, *, refresh_token: str) -> tuple[User, str, str]:
    try:
        payload = decode_token(refresh_token)
    except Exception as exc:
        if is_jwt_error(exc):
            raise InvalidRefreshTokenError()
        raise

    if payload.get("type") != "refresh":
        raise InvalidRefreshTokenError()

    sub = payload.get("sub")
    jti = payload.get("jti")
    if not sub or not jti:
        raise InvalidRefreshTokenError()

    try:
        user_id = UUID(str(sub))
    except Exception:
        raise InvalidRefreshTokenError()

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise InvalidRefreshTokenError()

    token_row = await db.scalar(
        select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.jti == str(jti))
    )
    if token_row is None or token_row.revoked:
        raise InvalidRefreshTokenError()

    # Rotation: revoke old and issue a new refresh token id.
    token_row.revoked = True

    new_token_jti = new_jti()
    new_row = RefreshToken(
        user_id=user_id, jti=new_token_jti, revoked=False, expires_at=refresh_expires_at()
    )
    db.add(new_row)
    await db.commit()

    access, refresh = issue_token_pair(user_id=str(user_id), refresh_jti=new_token_jti)
    return user, access, refresh

