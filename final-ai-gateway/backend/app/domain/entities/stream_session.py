"""
An SSE stream session that tracks event_id, checkpoint, and resume capability.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class StreamStatus(str, Enum):
    ACTIVE = "active"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StreamSession:
    session_id: str = field(default_factory=lambda: f"sse_{uuid.uuid4().hex[:12]}")
    request_id: str = ""
    run_id: Optional[str] = None
    stream_type: str = "chat"
    last_event_id: int = 0
    status: StreamStatus = StreamStatus.ACTIVE
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
