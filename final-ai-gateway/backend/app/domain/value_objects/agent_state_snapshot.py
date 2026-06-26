"""
A snapshot of agent state at a checkpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentStateSnapshot:
    run_id: str
    node_name: str
    state: dict[str, Any] = field(default_factory=dict)
    event_id: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))