"""
A compute slot in the local model backend (llama.cpp slot abstraction).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class SlotStatus(str, Enum):
    IDLE = "idle"
    BUSY = "busy"
    SAVING = "saving"
    UNAVAILABLE = "unavailable"


@dataclass
class Slot:
    slot_id: int
    status: SlotStatus = SlotStatus.IDLE
    current_request_id: Optional[str] = None
    prompt_tokens: int = 0
    tokens_generated: int = 0
    prefix_hash: Optional[str] = None
    cached_prompt_tokens: int = 0
    allocated_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
