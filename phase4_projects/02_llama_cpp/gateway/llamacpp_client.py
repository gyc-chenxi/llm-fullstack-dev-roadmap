"""
llama-server 异步 HTTP 客户端
-----------------------------
设计原则（Gateway 模式的核心）：
  1. Gateway 不做任何推理，只做请求代理和结果转发
  2. 所有网络异常、超时、上游错误码在此统一收敛，route 层无需关心
  3. 流式（SSE）和非流式分别处理，避免将 SSE 流全量读入内存

数据流向：
  非流式：Gateways POST → upstream POST /v1/chat/completions
         → await r.json() + 注入 _gateway.latency_ms → 返回 dict

  流式：  Gateway POST → upstream POST /v1/chat/completions (stream=True)
         → httpx.stream() → aiter_bytes() → yield chunk 透传
         （不解析、不累积、不修改 SSE chunk 内容）
"""

import json
import time
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException

from gateway.config import settings


class LlamaCppClient:
    """
    llama-server 的异步 HTTP 客户端。

    生命周期：由 FastAPI lifespan 管理，应用启动时创建，关闭时释放连接池。
    连接复用：httpx.AsyncClient 底层维护连接池，跨请求复用 TCP 连接。
    """

    def __init__(self) -> None:
        """初始化上游 HTTP 客户端（单例，整个生命周期复用）。"""
        # 超时策略（覆盖 connect/read/write/pool 四个维度）
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
        """释放 httpx 连接池。"""
        await self._client.aclose()

    async def health(self) -> tuple[bool, str]:
        """
        健康检查：调用上游 /v1/models 端点。
        返回 (是否正常, 详情字符串)。
        """
        try:
            r = await self._client.get("/v1/models")
            if r.status_code == 200:
                return True, "llama-server ready"
            return False, f"llama-server returned {r.status_code}"
        except httpx.HTTPError as e:
            return False, repr(e)

    async def chat_completion(self, payload: dict) -> dict:
        """
        非流式调用（适用于 correctness 测试、JSON 输出、短请求）。

        处理流程：
          1. 计时开始
          2. POST /v1/chat/completions（超时 → 504，连接失败 → 502）
          3. 解析 JSON 响应（失败 → 502 Invalid JSON）
          4. 注入 _gateway.latency_ms 字段
          5. 返回 dict

        异常映射：
          - TimeoutException    → 504 UPSTREAM_TIMEOUT
          - HTTPStatusError     → 透传上游状态码
          - HTTPError           → 502 UPSTREAM_CONNECT_ERROR
          - JSONDecodeError     → 502 UPSTREAM_INVALID_JSON

        参数：
          payload: to_upstream_payload() 产出的 dict
            ├── model: str          ← 模型名称（默认/显式指定）
            ├── messages: list[dict] ← 聊天历史 [{role, content}, ...]
            ├── temperature: float  ← 采样温度 (0.0~2.0)
            ├── top_p: float        ← 核采样阈值 (0.0~1.0)
            ├── max_tokens: int     ← 最大输出 token 数
            └── stream: bool=false  ← 非流式模式

        返回：
          上游返回的 JSON 响应 dict（含 Gateway 注入的 _gateway 元数据）
            ├── id: str                    ← 上游生成的请求 ID
            ├── model: str                 ← 实际使用的模型名称
            ├── choices: list[dict]        ← 生成结果 [{message: {role, content}, ...}]
            ├── usage: dict                ← token 用量统计
            │   ├── prompt_tokens: int
            │   ├── completion_tokens: int
            │   └── total_tokens: int
            └── _gateway: dict             ← Gateway 注入的元数据
                └── latency_ms: float      ← 端到端下游延迟
        """
        t0 = time.perf_counter()
        try:
            r = await self._client.post("/v1/chat/completions", json=payload)
            r.raise_for_status()
            data = r.json()
            # 注入 Gateway 元数据（上游不感知）
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
        流式调用：直接将上游 SSE chunk 透传给 Gateway 的 StreamingResponse。

        关键约束：
          - 不能 await r.aread()（否则将流式响应变为阻塞响应）
          - 使用 async with self._client.stream(...) 逐字节迭代
          - 异常时不抛异常，而是 yield 一个 SSE error 事件
            （让客户端能正确处理上游超时，不会一直等待）

        参数：
          payload: 含 stream: true 的请求 dict

        Yields:
          bytes: 上游 SSE chunk 的原始字节（透传，不修改）
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
            # 超时时发送 SSE error 事件（Client 端会收到 event: error）
            yield f"event: error\ndata: {json.dumps({'error': 'upstream timeout', 'detail': repr(e)}, ensure_ascii=False)}\n\n".encode("utf-8")
        except httpx.HTTPStatusError as e:
            body = e.response.text[:2000]
            yield f"event: error\ndata: {json.dumps({'error': 'upstream status error', 'body': body}, ensure_ascii=False)}\n\n".encode("utf-8")
        except httpx.HTTPError as e:
            yield f"event: error\ndata: {json.dumps({'error': 'upstream http error', 'detail': repr(e)}, ensure_ascii=False)}\n\n".encode("utf-8")