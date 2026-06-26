"""
Admission decision value object returned by AdmissionController.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DecisionType(str, Enum):
    ADMIT = "admit"
    QUEUE = "queue"
    REJECT = "reject"
    DEGRADE = "degrade"
    LONG_CONTEXT = "long_context"


@dataclass
class AdmissionDecision:
    decision: DecisionType
    reason: str = ""
    slot_id: Optional[int] = None
    estimated_kv_bytes: float = 0.0
    estimated_wait_ms: int = 0
    queue_position: int = 0