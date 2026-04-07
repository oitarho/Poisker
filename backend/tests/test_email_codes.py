from __future__ import annotations

import pytest

from app.core.config import settings
from app.modules.auth.email_codes import (
    PURPOSE_RESET,
    PURPOSE_VERIFY,
    apply_rate_limits_after_send_attempt,
    can_send_code,
    confirm_code,
    generate_six_digit_code,
    hash_code,
    normalize_email,
    store_code_and_apply_rate_limits,
)
from tests.fake_async_redis import FakeAsyncRedis


@pytest.fixture
def fake_redis(monkeypatch):
    r = FakeAsyncRedis()
    monkeypatch.setattr("app.modules.auth.email_codes.get_redis", lambda: r)
    return r


def test_normalize_email():
    assert normalize_email(" Test@Example.COM ") == "test@example.com"


def test_generate_six_digit_code():
    for _ in range(50):
        c = generate_six_digit_code()
        assert len(c) == 6
        assert c.isdigit()
        assert c[0] != "0"


def test_hash_code_stable():
    h1 = hash_code(email="a@b.c", code="123456", purpose=PURPOSE_VERIFY)
    h2 = hash_code(email="a@b.c", code="123456", purpose=PURPOSE_VERIFY)
    assert h1 == h2
    assert len(h1) == 64


@pytest.mark.asyncio
async def test_confirm_success(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "code_ttl_seconds", 600)
    em = "user@example.com"
    code = "424242"
    await store_code_and_apply_rate_limits(purpose=PURPOSE_VERIFY, email=em, code=code)
    await confirm_code(purpose=PURPOSE_VERIFY, email=em, code=code)
    stored = await fake_redis.get(f"poisker:{PURPOSE_VERIFY}:hash:{normalize_email(em)}")
    assert stored is None


@pytest.mark.asyncio
async def test_confirm_wrong_code(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "code_ttl_seconds", 600)
    monkeypatch.setattr(settings, "code_max_failed_attempts", 5)
    em = "user@example.com"
    await store_code_and_apply_rate_limits(purpose=PURPOSE_VERIFY, email=em, code="111111")
    from app.modules.auth.email_codes import InvalidOrExpiredCodeError

    with pytest.raises(InvalidOrExpiredCodeError):
        await confirm_code(purpose=PURPOSE_VERIFY, email=em, code="222222")


@pytest.mark.asyncio
async def test_confirm_too_many_failures(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "code_ttl_seconds", 600)
    monkeypatch.setattr(settings, "code_max_failed_attempts", 2)
    em = "user@example.com"
    await store_code_and_apply_rate_limits(purpose=PURPOSE_VERIFY, email=em, code="111111")
    from app.modules.auth.email_codes import InvalidOrExpiredCodeError, TooManyFailedAttemptsError

    with pytest.raises(InvalidOrExpiredCodeError):
        await confirm_code(purpose=PURPOSE_VERIFY, email=em, code="222222")
    with pytest.raises(TooManyFailedAttemptsError):
        await confirm_code(purpose=PURPOSE_VERIFY, email=em, code="222222")


@pytest.mark.asyncio
async def test_resend_cooldown(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "code_resend_cooldown_seconds", 60)
    monkeypatch.setattr(settings, "code_max_sends_per_hour", 10)
    em = "u@example.com"
    await apply_rate_limits_after_send_attempt(purpose=PURPOSE_VERIFY, email=em)
    from app.core.errors import TooManyRequestsError

    with pytest.raises(TooManyRequestsError) as exc:
        await can_send_code(purpose=PURPOSE_VERIFY, email=em)
    assert exc.value.code == "resend_cooldown"


@pytest.mark.asyncio
async def test_hourly_limit(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "code_resend_cooldown_seconds", 0)
    monkeypatch.setattr(settings, "code_max_sends_per_hour", 2)
    em = "h@example.com"
    hk = f"poisker:{PURPOSE_VERIFY}:hour:{normalize_email(em)}"
    await fake_redis.set(hk, "2", ex=3600)
    from app.core.errors import TooManyRequestsError

    with pytest.raises(TooManyRequestsError) as exc:
        await can_send_code(purpose=PURPOSE_VERIFY, email=em)
    assert exc.value.code == "hourly_limit"


@pytest.mark.asyncio
async def test_password_reset_rate_limit_same_bucket(fake_redis, monkeypatch):
    monkeypatch.setattr(settings, "code_resend_cooldown_seconds", 0)
    monkeypatch.setattr(settings, "code_max_sends_per_hour", 1)
    em = "p@example.com"
    await apply_rate_limits_after_send_attempt(purpose=PURPOSE_RESET, email=em)
    from app.core.errors import TooManyRequestsError

    with pytest.raises(TooManyRequestsError):
        await can_send_code(purpose=PURPOSE_RESET, email=em)
