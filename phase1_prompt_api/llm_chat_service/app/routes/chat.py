"""POST /v1/chat/completions — 核心聊天路由"""

import json
import time
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from ..schemas.chat import ChatRequest, ChatResponse, ChatChoice, Usage, Message, StreamChunk, StreamChoice, DeltaContent
from ..config import settings
from ..auth import verify_api_key
from ..dependencies import get_llm_client

router = APIRouter(prefix="/v1", tags=["Chat"])


@router.post("/chat/completions", response_model=None)
async def chat_completions(
    req: ChatRequest,
    request: Request,
    _: None = Depends(verify_api_key) if settings.auth_enabled else None,
):
    """兼容 OpenAI 格式的聊天接口 — 支持流式与非流式"""
    client = get_llm_client(request)

    if req.stream:
        return StreamingResponse(
            _stream_chat(client, req, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        return await _non_stream_chat(client, req, request)


async def _non_stream_chat(client, req: ChatRequest, request: Request) -> dict:
    """非流式调用"""
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        response = await client.chat(
            messages=messages,
            model=req.model or settings.default_model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            top_p=req.top_p,
            stream=False,
        )
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=502, detail={
            "code": "UPSTREAM_ERROR",
            "message": str(e),
        })

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model or settings.default_model,
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response.content},
            "finish_reason": response.finish_reason or "stop",
        }],
        "usage": response.usage if response.usage else {
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
        },
    }


async def _stream_chat(client, req: ChatRequest, request: Request):
    """流式 SSE 生成器"""
    chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        async for token in client.chat_stream(
            messages=messages,
            model=req.model or settings.default_model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            top_p=req.top_p,
        ):
            chunk = {
                "id": chat_id,
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": req.model or settings.default_model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": token, "role": "assistant"},
                    "finish_reason": None,
                }],
            }
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        # 结束标记
        final = {
            "id": chat_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": req.model or settings.default_model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop",
            }],
        }
        yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        error = {"error": {"code": "STREAM_ERROR", "message": str(e)}}
        yield f"data: {json.dumps(error)}\n\n"
