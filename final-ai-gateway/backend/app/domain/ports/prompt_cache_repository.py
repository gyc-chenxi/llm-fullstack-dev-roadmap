"""
Prompt Cache Repository port — abstract interface for prompt cache storage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..value_objects.prefix_hash import PrefixHash


class PromptCacheRepositoryPort(ABC):
    @abstractmethod
    async def get(self, prefix_hash: str) -> Optional[dict]:
        ...

    @abstractmethod
    async def set(self, prefix_hash: str, slot_id: int, prefix_tokens: int) -> None:
        ...

    @abstractmethod
    async def delete(self, prefix_hash: str) -> None:
        ...

    @abstractmethod
    async def touch(self, prefix_hash: str) -> None:
        ...

    @abstractmethod
    async def get_all(self) -> list[dict]:
        ...
