from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.storage.base import Storage
from app.storage.local import LocalStorage


@lru_cache(maxsize=1)
def get_storage() -> Storage:
    # MVP: local filesystem storage. Designed to be swapped with S3-compatible later.
    return LocalStorage(base_dir=settings.media_dir, public_base=settings.media_public_base)

