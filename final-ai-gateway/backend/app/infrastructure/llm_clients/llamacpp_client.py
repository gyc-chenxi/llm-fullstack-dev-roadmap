"""
llama.cpp server client — OpenAI-compatible HTTP adapter.
Implements the LLMClientPort interface.
"""

from __future__ import annotations

import json
import time
import logging
from typing import AsyncIterator, Optional

import httpx

from app.domain.ports.llm_client import LLMClientPort

logger = logging.getLogger(__name__)


class LlamacppClient(LLMClientPort):
    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=10),
            )
        return self._client

    async def chat_completion(
        self,
        messages: list[dict],
        model: str = "",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        stream: bool = True,
        **kwargs,
    ) -> AsyncIterator[dict]:
        client = await self._get_client()
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": kwargs.get("top_p", 0.95),
            "stream": stream,
        }
        if kwargs.get("stop"):
            payload["stop"] = kwargs["stop"]

        if stream:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            yield {"type": "done"}
                            break
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get("choices", [])
                            if choices and choices[0].get("delta", {}).get("content"):
                                yield {
                                    "type": "token",
                                    "content": choices[0]["delta"]["content"],
                                }
                        except json.JSONDecodeError:
                            continue
        else:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                yield {
                    "type": "token",
                    "content": choices[0].get("message", {}).get("content", ""),
                }
            yield {"type": "done"}

    async def tokenize(self, text: str) -> list[int]:
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/tokenize",
                json={"content": text},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("tokens", [])
        except Exception:
            logger.warning("llama.cpp /tokenize failed, using fallback estimate", exc_info=True)
            return [0] * self._fallback_count(text)

    async def get_metrics(self) -> dict:
        client = await self._get_client()
        try:
            response = await client.get(f"{self.base_url}/metrics")
            response.raise_for_status()
            return {"raw": response.text, "source": "llamacpp"}
        except Exception as e:
            logger.warning("Failed to fetch llama.cpp metrics: %s", e)
            return {"error": str(e)}

    async def get_slots(self) -> list[dict]:
        client = await self._get_client()
        try:
            response = await client.get(f"{self.base_url}/slots")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning("Failed to fetch llama.cpp slots: %s", e)
            return []

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def _fallback_count(text: str) -> int:
        return max(1, len(text) // 3)

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
