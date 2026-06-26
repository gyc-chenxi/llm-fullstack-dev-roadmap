"""
Queue ticket for a request waiting in the Redis priority queue.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class QueueTicket:
    ticket_id: str = field(default_factory=lambda: f"ticket_{uuid.uuid4().hex[:12]}")
    request_id: str = ""
    run_id: Optional[str] = None
    priority: int = 5
    enqueued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dequeued_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3
