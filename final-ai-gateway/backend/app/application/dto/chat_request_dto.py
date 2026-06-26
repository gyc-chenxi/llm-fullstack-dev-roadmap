"""
Chat request DTO — input model for the chat endpoint.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequestDTO(BaseModel):
    messages: list[dict] = Field(..., min_length=1, description="Chat messages in OpenAI format")
    model: str = Field(default="qwen2.5:7b")
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)
    stream: bool = True
    priority: int = Field(default=5, ge=1, le=10)
    tenant_id: str = "default"
    stop: Optional[list[str]] = None


class ChatResponseDTO(BaseModel):
    request_id: str
    status: str
    stream_url: Optional[str] = None
    trace_id: Optional[str] = None
    queue_position: int = 0
    estimated_wait_ms: int = 0


class StreamResumeDTO(BaseModel):
    request_id: str
    last_event_id: int = 0


class CancelRequestDTO(BaseModel):
    request_id: str