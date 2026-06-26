"""
Trace collector — provides trace querying for the dashboard.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.domain.entities.trace_run import TraceRun
from app.domain.ports.trace_repository import TraceRepositoryPort

logger = logging.getLogger(__name__)


class TraceCollector:
    def __init__(self, trace_repo: TraceRepositoryPort):
        self.trace_repo = trace_repo

    async def get_trace(self, trace_id: str) -> Optional[TraceRun]:
        return await self.trace_repo.get(trace_id)

    async def get_recent(self, run_type: str = "", limit: int = 20) -> list[TraceRun]:
        return await self.trace_repo.query_recent(run_type=run_type, limit=limit)

    async def get_stats(self, window_sec: int = 3600) -> dict:
        return await self.trace_repo.get_summary_stats(window_sec=window_sec)
