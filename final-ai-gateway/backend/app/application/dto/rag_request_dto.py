"""
Chat response DTO — output model for chat responses.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class ChatResponseDTO(BaseModel):
    request_id: str
    status: str
    stream_url: Optional[str] = None
    trace_id: Optional[str] = None
    queue_position: int = 0
    estimated_wait_ms: int = 0