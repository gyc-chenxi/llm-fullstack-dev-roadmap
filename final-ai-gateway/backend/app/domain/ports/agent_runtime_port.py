"""
Agent Runtime port — abstract interface for the LangGraph agent execution runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, Any


class AgentRuntimePort(ABC):
    @abstractmethod
    async def run(
        self, run_id: str, goal: str, agent_type: str, max_steps: int = 20
    ) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    async def resume(
        self, run_id: str, last_event_id: int
    ) -> AsyncIterator[dict]:
        ...

    @abstractmethod
    async def cancel(self, run_id: str) -> bool:
        ...

    @abstractmethod
    async def get_state(self, run_id: str) -> dict[str, Any]:
        ...
