"""
Tokenizer implementations — llama.cpp tokenizer, tiktoken estimator, and fallback.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.domain.ports.tokenizer_port import TokenizerPort

logger = logging.getLogger(__name__)


class LlamacppTokenizer(TokenizerPort):
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
        return self._client

    async def count_tokens(self, text: str) -> int:
        tokens = await self.encode(text)
        return len(tokens)

    async def encode(self, text: str) -> list[int]:
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/tokenize",
                json={"content": text},
            )
            response.raise_for_status()
            return response.json().get("tokens", [])
        except Exception as e:
            logger.debug("llama.cpp tokenize failed: %s, using fallback", e)
            return [0] * max(1, len(text) // 3)

    async def decode(self, tokens: list[int]) -> str:
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.base_url}/detokenize",
                json={"tokens": tokens},
            )
            response.raise_for_status()
            return response.json().get("content", "")
        except Exception as e:
            logger.debug("llama.cpp detokenize failed: %s", e)
            return ""


class TiktokenEstimator(TokenizerPort):
    def __init__(self, encoding_name: str = "cl100k_base"):
        try:
            import tiktoken
            self._enc = tiktoken.get_encoding(encoding_name)
        except ImportError:
            self._enc = None

    async def count_tokens(self, text: str) -> int:
        if self._enc is not None:
            return len(self._enc.encode(text))
        return max(1, len(text) // 3)

    async def encode(self, text: str) -> list[int]:
        if self._enc is not None:
            return self._enc.encode(text)
        return [0] * max(1, len(text) // 3)

    async def decode(self, tokens: list[int]) -> str:
        if self._enc is not None:
            return self._enc.decode(tokens)
        return ""


class FallbackTokenizer(TokenizerPort):
    """Character-based fallback — ~3 chars per token for CJK, ~4 for Latin."""

    async def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 3)

    async def encode(self, text: str) -> list[int]:
        return [0] * self.count_tokens(text)

    async def decode(self, tokens: list[int]) -> str:
        return ""
