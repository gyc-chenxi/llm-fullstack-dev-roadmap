"""
Generic OpenAI-compatible client for any OpenAI API-compatible endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Optional

import httpx

from app.domain.ports.llm_client import LLMClientPort

logger = logging.getLogger(__name__)


class OpenAICompatibleClient(LLMClientPort):
    def __init__(self, base_url: str = "", api_key: str = "", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=headers,
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
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        if stream:
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=payload,
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
                                yield {"type": "token", "content": choices[0]["delta"]["content"]}
                        except json.JSONDecodeError:
                            continue
        else:
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                yield {"type": "token", "content": choices[0].get("message", {}).get("content", "")}
            yield {"type": "done"}

    async def tokenize(self, text: str) -> list[int]:
        return [0] * max(1, len(text) // 3)

    async def get_metrics(self) -> dict:
        return {"backend": "openai-compatible"}

    async def get_slots(self) -> list[dict]:
        return []

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/v1/models")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
