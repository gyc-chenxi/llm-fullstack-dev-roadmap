"""
Tokenizer port — abstract interface for text tokenization.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class TokenizerPort(ABC):
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        ...

    @abstractmethod
    async def encode(self, text: str) -> list[int]:
        ...

    @abstractmethod
    async def decode(self, tokens: list[int]) -> str:
        ...
