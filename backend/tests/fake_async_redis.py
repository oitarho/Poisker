"""
Minimal async Redis double for unit tests (no server).
"""

from __future__ import annotations

import time
from typing import Any


class FakeAsyncRedis:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}
        self._ttl: dict[str, float] = {}

    def _purge(self, key: str) -> None:
        exp = self._ttl.get(key)
        if exp is not None and time.time() > exp:
            self._data.pop(key, None)
            self._ttl.pop(key, None)

    def _purge_all(self) -> None:
        now = time.time()
        for k in list(self._ttl.keys()):
            if self._ttl.get(k) is not None and now > self._ttl[k]:
                self._data.pop(k, None)
                self._ttl.pop(k, None)

    async def get(self, key: str) -> str | None:
        self._purge(key)
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> bool | None:
        self._purge(key)
        if nx and key in self._data:
            return None
        self._data[key] = value
        if ex is not None:
            self._ttl[key] = time.time() + ex
        return True

    async def delete(self, *keys: str) -> int:
        n = 0
        for k in keys:
            if k in self._data:
                self._data.pop(k, None)
                self._ttl.pop(k, None)
                n += 1
        return n

    async def incr(self, key: str) -> int:
        self._purge(key)
        v = int(self._data.get(key, "0"))
        v += 1
        self._data[key] = str(v)
        return v

    async def expire(self, key: str, seconds: int) -> bool:
        self._purge(key)
        if key not in self._data:
            return False
        self._ttl[key] = time.time() + seconds
        return True

    async def exists(self, key: str) -> int:
        self._purge(key)
        return 1 if key in self._data else 0
