from __future__ import annotations

import redis.asyncio as redis

from app.core.config import settings


def get_redis() -> redis.Redis:
    # Create-on-demand client; keep it simple for MVP.
    # redis-py maintains its own connection pool.
    return redis.from_url(settings.redis_url, decode_responses=True)
