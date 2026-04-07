from __future__ import annotations

import os
from pathlib import Path

from app.storage.base import StoredFile, Storage


class LocalStorage(Storage):
    def __init__(self, base_dir: str = "var/media", public_base: str = "/media") -> None:
        self._base_dir = Path(base_dir)
        self._public_base = public_base.rstrip("/")
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        safe_key = key.lstrip("/").replace("..", "_")
        return self._base_dir / safe_key

    async def put_bytes(
        self, *, key: str, data: bytes, content_type: str | None = None
    ) -> StoredFile:
        p = self._path_for_key(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return StoredFile(key=key, content_type=content_type, size_bytes=len(data))

    async def delete(self, *, key: str) -> None:
        p = self._path_for_key(key)
        try:
            os.remove(p)
        except FileNotFoundError:
            return

    def public_url(self, *, key: str) -> str:
        return f"{self._public_base}/{key.lstrip('/')}"
