import json
import time
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException

from gateway.config import settings


class LlamaCppClient:
    """
    llama-server 的异步 HTTP 客户端。
    设计原则：
    1. Gateway 不直接做推理，只代理上游 OpenAI-compatible API。
    2. 所有超时、异常、状态码在这里统一收敛。
    3. stream 和 non-stream 分开处理，避免把 SSE 全量读入内存。
    """

    def __init__(self) -> None:
        timeout = httpx.Timeout(
            connect=settings.upstream_connect_timeout,
            read=settings.upstream_read_timeout,
            write=30.0,
            pool=30.0,
        )
        headers = {}
        if settings.llamacpp_api_key:
            headers["Authorization"] = f"Bearer {settings.llamacpp_api_key}"

        self._client = httpx.AsyncClient(
            base_url=settings.llamacpp_base_url,
            timeout=timeout,
            headers=headers,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def health(self) -> tuple[bool, str]:
        try:
            r = await self._client.get("/v1/models")
            if r.status_code == 200:
                return True, "llama-server ready"
            return False, f"llama-server returned {r.status_code}"
        except httpx.HTTPError as e:
            return False, repr(e)

    async def chat_completion(self, payload: dict) -> dict:
        """
        非流式调用。适合压测 correctness、JSON 输出、短请求。
        """
        t0 = time.perf_counter()
        try:
            r = await self._client.post("/v1/chat/completions", json=payload)
            r.raise_for_status()
            data = r.json()
            data.setdefault("_gateway", {})
            data["_gateway"]["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            return data
        except httpx.TimeoutException as e:
            raise HTTPException(status_code=504, detail=f"upstream timeout: {e!r}") from e
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail={
                    "message": "upstream llama-server error",
                    "body": e.response.text[:2000],
                },
            ) from e
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"upstream http error: {e!r}") from e
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"invalid upstream json: {e!r}") from e

    async def stream_chat_completion(self, payload: dict) -> AsyncIterator[bytes]:
        """
        流式调用。直接把上游 SSE chunk 透传给前端。
        关键点：不能 await r.aread()，否则会把流式响应变成阻塞响应。
        """
        try:
            async with self._client.stream(
                "POST",
                "/v1/chat/completions",
                json=payload,
            ) as r:
                r.raise_for_status()
                async for chunk in r.aiter_bytes():
                    if chunk:
                        yield chunk
        except httpx.TimeoutException as e:
            yield f"event: error\ndata: {json.dumps({'error': 'upstream timeout', 'detail': repr(e)}, ensure_ascii=False)}\n\n".encode("utf-8")
        except httpx.HTTPStatusError as e:
            body = e.response.text[:2000]
            yield f"event: error\ndata: {json.dumps({'error': 'upstream status error', 'body': body}, ensure_ascii=False)}\n\n".encode("utf-8")
        except httpx.HTTPError as e:
            yield f"event: error\ndata: {json.dumps({'error': 'upstream http error', 'detail': repr(e)}, ensure_ascii=False)}\n\n".encode("utf-8")