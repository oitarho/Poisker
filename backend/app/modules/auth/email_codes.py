from __future__ import annotations

import hashlib
import secrets
from typing import Literal

import redis.asyncio as redis

from app.core.config import settings
from app.core.errors import AppError, TooManyRequestsError
from app.integrations.redis import get_redis

PURPOSE_VERIFY = "ev"
PURPOSE_RESET = "pr"


def normalize_email(email: str) -> str:
    return email.lower().strip()


def generate_six_digit_code() -> str:
    n = secrets.randbelow(900_000) + 100_000
    return f"{n:06d}"


def hash_code(*, email: str, code: str, purpose: str) -> str:
    em = normalize_email(email)
    pepper = settings.code_pepper_effective
    raw = f"{pepper}:{em}:{purpose}:{code}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _key_hash(purpose: str, email: str) -> str:
    return f"poisker:{purpose}:hash:{normalize_email(email)}"


def _key_fail(purpose: str, email: str) -> str:
    return f"poisker:{purpose}:fail:{normalize_email(email)}"


def _key_cooldown(purpose: str, email: str) -> str:
    return f"poisker:{purpose}:cooldown:{normalize_email(email)}"


def _key_hour(purpose: str, email: str) -> str:
    return f"poisker:{purpose}:hour:{normalize_email(email)}"


def _key_block(purpose: str, email: str) -> str:
    return f"poisker:{purpose}:block:{normalize_email(email)}"


def _r() -> redis.Redis:
    return get_redis()


class InvalidOrExpiredCodeError(AppError):
    def __init__(self, message: str = "Invalid or expired code") -> None:
        super().__init__(code="invalid_code", message=message, status_code=400)


class TooManyFailedAttemptsError(AppError):
    def __init__(self) -> None:
        super().__init__(
            code="too_many_attempts",
            message="Too many incorrect attempts. Request a new code.",
            status_code=400,
        )


async def _ensure_not_blocked(r: redis.Redis, purpose: str, email: str) -> None:
    if await r.exists(_key_block(purpose, email)):
        raise TooManyRequestsError(code="temporarily_blocked", message="Too many attempts. Try again later.")


async def can_send_code(*, purpose: str, email: str) -> None:
    """Raises TooManyRequestsError if cooldown or hourly cap applies."""
    r = _r()
    em = normalize_email(email)
    await _ensure_not_blocked(r, purpose, em)
    if await r.exists(_key_cooldown(purpose, em)):
        raise TooManyRequestsError(
            code="resend_cooldown",
            message=f"Please wait {settings.code_resend_cooldown_seconds} seconds before requesting again.",
        )
    hour_key = _key_hour(purpose, em)
    cnt = await r.get(hour_key)
    if cnt is not None and int(cnt) >= settings.code_max_sends_per_hour:
        raise TooManyRequestsError(
            code="hourly_limit",
            message="Too many messages sent to this email. Try again later.",
        )


async def apply_rate_limits_after_send_attempt(*, purpose: str, email: str) -> None:
    """Cooldown + hourly counter (used after any send attempt, including password-reset no-op)."""
    r = _r()
    em = normalize_email(email)
    await r.set(_key_cooldown(purpose, em), "1", ex=settings.code_resend_cooldown_seconds)
    hk = _key_hour(purpose, em)
    n = await r.incr(hk)
    if n == 1:
        await r.expire(hk, 3600)


async def store_code_and_apply_rate_limits(*, purpose: str, email: str, code: str) -> None:
    """Store hashed code, reset fail counter, apply cooldown + hourly counter."""
    r = _r()
    em = normalize_email(email)
    hk = _key_hash(purpose, em)
    fk = _key_fail(purpose, em)
    await r.set(hk, hash_code(email=em, code=code, purpose=purpose), ex=settings.code_ttl_seconds)
    await r.delete(fk)
    await apply_rate_limits_after_send_attempt(purpose=purpose, email=em)


async def invalidate_code(*, purpose: str, email: str) -> None:
    r = _r()
    em = normalize_email(email)
    await r.delete(_key_hash(purpose, em), _key_fail(purpose, em))


async def confirm_code(
    *,
    purpose: str,
    email: str,
    code: str,
) -> Literal["ok"]:
    if not code.isdigit() or len(code) != 6:
        raise InvalidOrExpiredCodeError("Code must be a 6-digit number")

    r = _r()
    em = normalize_email(email)
    await _ensure_not_blocked(r, purpose, em)

    hk = _key_hash(purpose, em)
    stored = await r.get(hk)
    if stored is None:
        raise InvalidOrExpiredCodeError("Invalid or expired code")

    expected = hash_code(email=em, code=code, purpose=purpose)
    if secrets.compare_digest(stored, expected):
        await r.delete(hk, _key_fail(purpose, em), _key_cooldown(purpose, em))
        return "ok"

    fk = _key_fail(purpose, em)
    fails = await r.incr(fk)
    if fails == 1:
        await r.expire(fk, settings.code_ttl_seconds)

    if fails >= settings.code_max_failed_attempts:
        await r.delete(hk, fk)
        await r.set(_key_block(purpose, em), "1", ex=min(900, settings.code_ttl_seconds * 2))
        raise TooManyFailedAttemptsError()

    raise InvalidOrExpiredCodeError("Invalid or expired code")
