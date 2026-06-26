"""
An SSE stream event with event_id for resume capability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class StreamEvent:
    event_id: int
    request_id: str
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_sse_format(self) -> str:
        import json

        payload = {
            "event_id": self.event_id,
            "request_id": self.request_id,
            "type": self.event_type,
            **self.data,
            "created_at": int(self.created_at.timestamp()),
        }
        return f"data: {json.dumps(payload)}\n\n"