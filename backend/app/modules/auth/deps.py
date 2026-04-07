from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.errors import UnauthorizedError
from app.core.security import decode_token, is_jwt_error
from app.modules.users.models import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: DbSession,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if creds is None or not creds.credentials:
        raise UnauthorizedError()

    token = creds.credentials
    try:
        payload = decode_token(token)
    except Exception as exc:
        if is_jwt_error(exc):
            raise UnauthorizedError()
        raise

    if payload.get("type") != "access":
        raise UnauthorizedError()

    sub = payload.get("sub")
    try:
        user_id = UUID(str(sub))
    except Exception:
        raise UnauthorizedError()

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise UnauthorizedError()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_user_optional(
    db: DbSession,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User | None:
    if creds is None or not creds.credentials:
        return None
    try:
        return await get_current_user(db, creds)
    except Exception:
        return None


OptionalCurrentUser = Annotated[User | None, Depends(get_current_user_optional)]

