"""
LLM Client port — abstract interface for all model backend clients.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class LLMClientPort(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict],
        model: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = True,
        **kwargs,
    ) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    async def tokenize(self, text: str) -> list[int]:
        ...

    @abstractmethod
    async def get_metrics(self) -> dict:
        ...

    @abstractmethod
    async def get_slots(self) -> list[dict]:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
