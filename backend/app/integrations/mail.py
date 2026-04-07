from __future__ import annotations

import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

import anyio

from app.core.config import settings
from app.core.logging import get_logger


def _build_message(*, to_addr: str, subject: str, body_text: str) -> MIMEText:
    msg = MIMEText(body_text, "plain", "utf-8")
    msg["Subject"] = str(Header(subject, "utf-8"))
    msg["From"] = formataddr((settings.smtp_from_name, settings.smtp_from_email))
    msg["To"] = to_addr
    return msg


def _send_sync(to_addr: str, subject: str, body_text: str) -> None:
    if not settings.smtp_enabled:
        log = get_logger()
        log.warning(
            "smtp_disabled_skip_send",
            to_domain=to_addr.split("@")[-1] if "@" in to_addr else "",
            subject=subject[:80],
        )
        return

    msg = _build_message(to_addr=to_addr, subject=subject, body_text=body_text)

    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)


async def send_email(*, to_addr: str, subject: str, body_text: str) -> None:
    """Send a plain-text email via SMTP (blocking work runs in a thread)."""
    await anyio.to_thread.run_sync(_send_sync, to_addr, subject, body_text)


def verification_email_text(*, code: str) -> str:
    return (
        "Здравствуйте!\n\n"
        f"Ваш код подтверждения email для Poisker: {code}\n\n"
        "Код действителен 10 минут. Если вы не регистрировались в Poisker, проигнорируйте это письмо.\n"
    )


def password_reset_email_text(*, code: str) -> str:
    return (
        "Здравствуйте!\n\n"
        f"Ваш код для сброса пароля Poisker: {code}\n\n"
        "Код действителен 10 минут. Если вы не запрашивали сброс, проигнорируйте это письмо.\n"
    )

