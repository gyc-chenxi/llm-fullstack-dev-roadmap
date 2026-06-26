"""
Trace run capturing the full observability span tree for a request.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class TraceRun:
    trace_id: str = field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:12]}")
    request_id: str = ""
    run_type: str = "chat"
    spans: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    ttft_ms: float = 0.0
    tpot_ms: float = 0.0
    queue_wait_ms: float = 0.0
    model_backend: str = ""
    slot_id: Optional[int] = None
    retrieval_hits: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    final_status: str = "created"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
