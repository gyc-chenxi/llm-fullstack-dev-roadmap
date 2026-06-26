"""
Ollama client — OpenAI-compatible adapter for Ollama models.
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Optional

import httpx

from app.domain.ports.llm_client import LLMClientPort

logger = logging.getLogger(__name__)


class OllamaClient(LLMClientPort):
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout))
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
        model_name = model or "qwen2.5"
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": stream,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": kwargs.get("top_p", 0.95),
            },
        }

        if stream:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                        if chunk.get("done"):
                            yield {"type": "done"}
                            break
                        msg = chunk.get("message", {})
                        if msg.get("content"):
                            yield {"type": "token", "content": msg["content"]}
                    except json.JSONDecodeError:
                        continue
        else:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={**payload, "stream": False},
            )
            response.raise_for_status()
            data = response.json()
            yield {"type": "token", "content": data.get("message", {}).get("content", "")}
            yield {"type": "done"}

    async def tokenize(self, text: str) -> list[int]:
        return [0] * max(1, len(text) // 3)

    async def get_metrics(self) -> dict:
        return {"backend": "ollama", "note": "limited metrics"}

    async def get_slots(self) -> list[dict]:
        return []

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
