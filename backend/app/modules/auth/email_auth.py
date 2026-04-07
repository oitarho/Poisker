from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.core.security import hash_password
from app.integrations.mail import (
    password_reset_email_text,
    send_email,
    verification_email_text,
)
from app.modules.auth.email_codes import (
    PURPOSE_RESET,
    PURPOSE_VERIFY,
    apply_rate_limits_after_send_attempt,
    can_send_code,
    confirm_code,
    generate_six_digit_code,
    normalize_email,
    store_code_and_apply_rate_limits,
)
from app.modules.users.models import RefreshToken, User


PASSWORD_RESET_OK_MESSAGE = "If an account exists for this email, we sent instructions."


async def send_verification_email_flow(db: AsyncSession, *, email: str) -> str:
    """
    Send verification code. Returns 'sent' or 'already_verified'.
    Raises NotFoundError if user does not exist.
    """
    em = normalize_email(email)
    user = await db.scalar(select(User).where(User.email == em))
    if user is None:
        raise NotFoundError("User not found")
    if user.is_email_verified:
        return "already_verified"

    await can_send_code(purpose=PURPOSE_VERIFY, email=em)
    code = generate_six_digit_code()
    await store_code_and_apply_rate_limits(purpose=PURPOSE_VERIFY, email=em, code=code)
    await send_email(
        to_addr=user.email,
        subject="Poisker: подтверждение email",
        body_text=verification_email_text(code=code),
    )
    return "sent"


async def send_verification_after_register(db: AsyncSession, *, email: str) -> None:
    """Called after successful registration; failures are logged, registration still succeeds."""
    log = get_logger()
    em = normalize_email(email)
    try:
        await can_send_code(purpose=PURPOSE_VERIFY, email=em)
        code = generate_six_digit_code()
        await store_code_and_apply_rate_limits(purpose=PURPOSE_VERIFY, email=em, code=code)
        user = await db.scalar(select(User).where(User.email == em))
        if user is None:
            log.error("verify_after_register_user_missing", email_domain=em.split("@")[-1])
            return
        await send_email(
            to_addr=user.email,
            subject="Poisker: подтверждение email",
            body_text=verification_email_text(code=code),
        )
    except Exception:
        log.exception("verification_email_after_register_failed", email_domain=em.split("@")[-1])


async def confirm_email_verification(db: AsyncSession, *, email: str, code: str) -> str:
    em = normalize_email(email)
    user = await db.scalar(select(User).where(User.email == em))
    if user is None:
        raise NotFoundError("User not found")
    if user.is_email_verified:
        return "already_verified"
    await confirm_code(purpose=PURPOSE_VERIFY, email=em, code=code)
    user.is_email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return "verified"


async def request_password_reset(db: AsyncSession, *, email: str) -> None:
    """Always completes without leaking existence; sends email only when user exists."""
    em = normalize_email(email)
    await can_send_code(purpose=PURPOSE_RESET, email=em)
    user = await db.scalar(select(User).where(User.email == em))
    if user is None:
        await apply_rate_limits_after_send_attempt(purpose=PURPOSE_RESET, email=em)
        return

    code = generate_six_digit_code()
    await store_code_and_apply_rate_limits(purpose=PURPOSE_RESET, email=em, code=code)
    await send_email(
        to_addr=user.email,
        subject="Poisker: сброс пароля",
        body_text=password_reset_email_text(code=code),
    )


async def confirm_password_reset(
    db: AsyncSession, *, email: str, code: str, new_password: str
) -> None:
    em = normalize_email(email)
    await confirm_code(purpose=PURPOSE_RESET, email=em, code=code)
    user = await db.scalar(select(User).where(User.email == em))
    if user is None:
        raise NotFoundError("User not found")

    user.password_hash = hash_password(new_password)
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
    await db.commit()
