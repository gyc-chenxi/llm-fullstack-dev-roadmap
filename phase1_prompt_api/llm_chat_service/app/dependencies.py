"""依赖注入 — 获取 LLM Client 实例"""

from fastapi import Request
import httpx
from dataclasses import dataclass
from typing import AsyncGenerator

from .config import settings


@dataclass
class SimpleLLMResponse:
    """简化的 LLM 响应，不依赖外部 client"""
    content: str
    model: str = ""
    finish_reason: str = "stop"
    usage: dict | None = None


class SimpleOpenAIClient:
    """最小化 OpenAI 兼容客户端 — 用于 Chat Service Demo"""

    def __init__(self, http_client: httpx.AsyncClient):
        self.http = http_client

    async def chat(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 1.0,
        stream: bool = False,
    ) -> SimpleLLMResponse:
        api_key = settings.openai_api_key or settings.deepseek_api_key
        base_url = settings.openai_base_url

        # 自动检测 DeepSeek 模型
        if "deepseek" in model.lower():
            api_key = settings.deepseek_api_key or api_key
            base_url = settings.deepseek_base_url

        if not api_key:
            raise RuntimeError(
                "未配置 API Key。请设置环境变量 OPENAI_API_KEY 或 DEEPSEEK_API_KEY"
            )

        resp = await self.http.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": False,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        return SimpleLLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", model),
            finish_reason=choice.get("finish_reason", "stop"),
            usage=data.get("usage", {}),
        )

    async def chat_stream(
        self,
        messages: list[dict],
        model: str = "gpt-4o-mini",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 1.0,
    ) -> AsyncGenerator[str, None]:
        api_key = settings.openai_api_key or settings.deepseek_api_key
        base_url = settings.openai_base_url

        if "deepseek" in model.lower():
            api_key = settings.deepseek_api_key or api_key
            base_url = settings.deepseek_base_url

        if not api_key:
            raise RuntimeError("未配置 API Key")

        async with self.http.stream(
            "POST",
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line.strip() != "data: [DONE]":
                    try:
                        chunk = __import__("json").loads(line[6:])
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                    except Exception:
                        continue


def get_llm_client(request: Request) -> SimpleOpenAIClient:
    """从 app.state 获取或创建 LLM Client"""
    http_client = request.app.state.http_client
    return SimpleOpenAIClient(http_client)
