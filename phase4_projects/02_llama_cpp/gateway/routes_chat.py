"""
聊天补全路由
-----------
对外提供 OpenAI 兼容的 /v1/chat/completions 端点。
前端、LangChain、OpenAI SDK 均可将 Gateway 当作 base_url 使用。

数据流向：
  客户端 POST /v1/chat/completions (JSON)
    → ChatCompletionRequest (Pydantic 校验)
    → to_upstream_payload(default_model)
      ├── 输入: {
      │     "model": str|None, "messages": [{role, content}, ...],
      │     "temperature": 0.2, "top_p": 0.9, "max_tokens": 512, "stream": bool,
      │     "extra_body": {...}  ← 透传字段（grammar, stop 等）
      │   }
      └── 输出: {
            "model": str,          ← None 被 default_model 填充
            "messages": [...],     ← ChatMessage 序列化为 dict
            "temperature": 0.2,    ← 保留 Gateway 默认值
            "top_p": 0.9,
            "max_tokens": 512,
            "stream": bool,        ← 转发给上游
            ...                    ← extra_body 合并到顶层
          }
    ┌→ 非流式: LlamaCppClient.chat_completion() → ORJSONResponse
    │           输出: {id, model, choices: [{message: {role, content}}], usage, _gateway}
    │           _gateway.latency_ms 由客户端注入
    └→ 流式:   LlamaCppClient.stream_chat_completion()
                输出: SSE bytes 透传，不解析不修改
                event: message\ndata: {"choices":[{"delta":{"content":"..."}}]}\n\n
                ... 逐 chunk 透传 ...
                data: [DONE]\n\n
"""

from fastapi import APIRouter, Request
from fastapi.responses import ORJSONResponse, StreamingResponse

from gateway.config import settings
from gateway.schemas import ChatCompletionRequest

router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    """
    核心聊天补全端点。

    根据 req.stream 决定返回类型：
      - stream=False → ORJSONResponse（非流式，等待完整响应后返回）
      - stream=True  → StreamingResponse（SSE 流式，逐 token 推送）

    参数：
      req: ChatCompletionRequest — Pydantic 校验后的请求体
      request: FastAPI Request — 用于获取 app.state.llamacpp 客户端

    返回：
      ORJSONResponse 或 StreamingResponse
    """
    # 从应用状态中获取 LlamaCppClient 单例（由 lifespan 创建）
    client = request.app.state.llamacpp
    # 将 Gateway 请求体转换为上游 payload（填充 default_model、序列化 messages 等）
    payload = req.to_upstream_payload(default_model=settings.default_model)

    if req.stream:
        # 流式模式：直接返回 StreamingResponse，上游 SSE chunk 透传
        return StreamingResponse(
            client.stream_chat_completion(payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",         # 禁止浏览器/代理缓存 SSE
                "X-Accel-Buffering": "no",            # 禁用 nginx 缓冲（如前端有 nginx 反向代理）
            },
        )

    # 非流式模式：等待上游完整响应后返回
    data = await client.chat_completion(payload)
    return ORJSONResponse(data)