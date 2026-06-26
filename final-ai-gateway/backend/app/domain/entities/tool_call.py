"""
A tool call executed by an agent during its run.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class ToolCall:
    tool_call_id: str = field(default_factory=lambda: f"tool_{uuid.uuid4().hex[:12]}")
    run_id: str = ""
    tool_name: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    input_payload: dict[str, Any] = field(default_factory=dict)
    output_payload: Any = None
    latency_ms: float = 0.0
    status: str = "pending"
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
