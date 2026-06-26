"""
Trace snapshot DTO.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class TraceSnapshotDTO(BaseModel):
    trace_id: str
    request_id: str
    run_type: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    ttft_ms: float
    tpot_ms: float
    queue_wait_ms: float
    model_backend: str
    slot_id: Optional[int]
    final_status: str
    spans: list[dict[str, Any]] = []
    tool_calls: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []