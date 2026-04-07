from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_jti() -> str:
    # 32 bytes -> 64 hex chars; fits RefreshToken.jti length
    return secrets.token_hex(32)


def refresh_expires_at() -> datetime:
    return _utcnow() + timedelta(seconds=settings.jwt_refresh_ttl_seconds)


def issue_token_pair(*, user_id: str, refresh_jti: str) -> tuple[str, str]:
    access = create_access_token(subject=user_id)
    refresh = create_refresh_token(subject=user_id, claims={"jti": refresh_jti})
    return access, refresh

