from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoredFile:
    key: str
    content_type: str | None
    size_bytes: int


class Storage(ABC):
    @abstractmethod
    async def put_bytes(
        self, *, key: str, data: bytes, content_type: str | None = None
    ) -> StoredFile:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, *, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def public_url(self, *, key: str) -> str:
        raise NotImplementedError
