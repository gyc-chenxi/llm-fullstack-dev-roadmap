"""
A unique inference request flowing through the gateway.
Represents the core entity tracked from admission to completion.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RequestStatus(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    ADMITTED = "admitted"
    STREAMING = "streaming"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    CIRCUIT_BROKEN = "circuit_broken"


@dataclass
class InferenceRequest:
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")
    tenant_id: str = "default"
    messages: list[dict] = field(default_factory=list)
    model: str = "qwen2.5-7b-instruct-q4_k_m"
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.95
    stream: bool = True
    priority: int = 5
    status: RequestStatus = RequestStatus.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    estimated_prompt_tokens: int = 0
    estimated_total_tokens: int = 0
    prefix_hash: Optional[str] = None
    slot_id: Optional[int] = None

    def __post_init__(self):
        if not self.messages:
            raise ValueError("messages must not be empty")
