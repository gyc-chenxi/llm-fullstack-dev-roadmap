"""
Agent loop guard — prevents infinite loops in agent execution.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from ..entities.fault_event import FaultEvent, FaultType


@dataclass
class AgentLoopGuard:
    max_steps: int = 20
    max_llm_calls: int = 15
    max_tool_calls: int = 10
    tool_timeout_ms: int = 30000
    same_tool_repeat_limit: int = 3
    same_message_repeat_limit: int = 5
    max_runtime_seconds: int = 300

    step_count: int = 0
    llm_call_count: int = 0
    tool_call_count: int = 0
    recent_tool_names: list[str] = field(default_factory=list)
    recent_messages: list[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.monotonic)

    def check_step(self) -> Optional[FaultEvent]:
        self.step_count += 1
        if self.step_count > self.max_steps:
            return FaultEvent(
                fault_type=FaultType.AGENT_LOOP,
                message=f"exceeded max steps: {self.step_count} > {self.max_steps}",
                detail={"step_count": self.step_count, "max_steps": self.max_steps},
            )
        if self._check_runtime_exceeded():
            return FaultEvent(
                fault_type=FaultType.AGENT_LOOP,
                message="agent runtime exceeded",
                detail={"runtime_sec": time.monotonic() - self.start_time},
            )
        return None

    def check_llm_call(self) -> Optional[FaultEvent]:
        self.llm_call_count += 1
        if self.llm_call_count > self.max_llm_calls:
            return FaultEvent(
                fault_type=FaultType.AGENT_LOOP,
                message=f"exceeded max LLM calls: {self.llm_call_count} > {self.max_llm_calls}",
            )
        return None

    def check_tool_call(self, tool_name: str) -> Optional[FaultEvent]:
        self.tool_call_count += 1
        self.recent_tool_names.append(tool_name)
        if self.tool_call_count > self.max_tool_calls:
            return FaultEvent(
                fault_type=FaultType.AGENT_LOOP,
                message=f"exceeded max tool calls: {self.tool_call_count} > {self.max_tool_calls}",
            )
        if self._check_tool_repeat(tool_name):
            return FaultEvent(
                fault_type=FaultType.AGENT_LOOP,
                message=f"tool {tool_name} called too many times consecutively",
                detail={"tool_name": tool_name, "repeat_limit": self.same_tool_repeat_limit},
            )
        return None

    def _check_tool_repeat(self, tool_name: str) -> bool:
        if len(self.recent_tool_names) < self.same_tool_repeat_limit:
            return False
        return self.recent_tool_names[-self.same_tool_repeat_limit:] == [tool_name] * self.same_tool_repeat_limit

    def _check_runtime_exceeded(self) -> bool:
        return (time.monotonic() - self.start_time) > self.max_runtime_seconds

    def reset(self):
        self.step_count = 0
        self.llm_call_count = 0
        self.tool_call_count = 0
        self.recent_tool_names.clear()
        self.recent_messages.clear()
        self.start_time = time.monotonic()