"""
An Agent execution run, representing a stateful agent task.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class AgentState(str, Enum):
    CREATED = "created"
    CLASSIFYING = "classifying"
    RETRIEVING = "retrieving"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentRun:
    run_id: str = field(default_factory=lambda: f"agent_{uuid.uuid4().hex[:12]}")
    tenant_id: str = "default"
    agent_type: str = "rag_agent"
    goal: str = ""
    state: AgentState = AgentState.CREATED
    max_steps: int = 20
    current_step: int = 0
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    checkpoint_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    messages: list[dict[str, Any]] = field(default_factory=list)
    retrieved_docs: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    trace_id: Optional[str] = None

    def __post_init__(self):
        if not self.goal.strip():
            raise ValueError("goal must not be empty")
