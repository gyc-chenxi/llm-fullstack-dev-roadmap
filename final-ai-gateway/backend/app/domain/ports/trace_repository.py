"""
Trace Repository port — abstract interface for trace data storage and query.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from ..entities.trace_run import TraceRun


class TraceRepositoryPort(ABC):
    @abstractmethod
    async def save(self, trace: TraceRun) -> None:
        ...

    @abstractmethod
    async def get(self, trace_id: str) -> Optional[TraceRun]:
        ...

    @abstractmethod
    async def query_recent(self, run_type: str = "", limit: int = 20) -> list[TraceRun]:
        ...

    @abstractmethod
    async def get_summary_stats(self, window_sec: int = 3600) -> dict[str, Any]:
        ...
