"""
Chat Routes — POST /api/v1/chat, GET stream, GET resume, POST cancel.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.responses import StreamingResponse

from app.application.dto.chat_request_dto import ChatRequestDTO, ChatResponseDTO, CancelRequestDTO, StreamResumeDTO
from app.application.orchestrators.inference_orchestrator import InferenceOrchestrator
from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


def get_orchestrator(request: Request) -> InferenceOrchestrator:
    return request.app.state.inference_orchestrator


def get_stream_session_repo(request: Request) -> RedisStreamSessionRepo:
    return request.app.state.stream_session_repo


@router.post("", response_model=ChatResponseDTO)
async def submit_chat(
    body: ChatRequestDTO,
    request: Request,
    orchestrator: InferenceOrchestrator = Depends(get_orchestrator),
):
    """Submit a chat completion request. Returns request_id and stream URL."""
    result = await orchestrator.submit(
        messages=body.messages,
        model=body.model,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        stream=body.stream,
        priority=body.priority,
        tenant_id=body.tenant_id,
    )
    # Store messages for stream retrieval
    stream_session_repo = request.app.state.stream_session_repo
    await stream_session_repo.store_messages(result["request_id"], body.messages,
                                              body.model, body.max_tokens, body.temperature)
    return ChatResponseDTO(**result)


@router.get("/{request_id}/stream")
async def stream_chat(
    request_id: str,
    request: Request,
    orchestrator: InferenceOrchestrator = Depends(get_orchestrator),
    stream_session_repo: RedisStreamSessionRepo = Depends(get_stream_session_repo),
):
    """SSE token stream for a submitted chat request."""
    session = await stream_session_repo.get_session(request_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    params = await stream_session_repo.get_messages(request_id)
    if params is None:
        raise HTTPException(status_code=400, detail="No messages stored for this request")

    return StreamingResponse(
        orchestrator.stream(
            request_id=request_id,
            messages=params["messages"],
            model=params.get("model", "qwen2.5:7b"),
            max_tokens=params.get("max_tokens", 2048),
            temperature=params.get("temperature", 0.7),
            slot_id=0,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{request_id}/resume")
async def resume_stream(
    request_id: str,
    last_event_id: int = 0,
    orchestrator: InferenceOrchestrator = Depends(get_orchestrator),
):
    """Resume an SSE stream from last_event_id for disconnected clients."""
    return StreamingResponse(
        orchestrator.resume(request_id, last_event_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
        },
    )


@router.post("/{request_id}/cancel")
async def cancel_request(
    request_id: str,
    orchestrator: InferenceOrchestrator = Depends(get_orchestrator),
):
    """Cancel a queued or streaming request."""
    result = await orchestrator.cancel(request_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Request not found")
    return result
