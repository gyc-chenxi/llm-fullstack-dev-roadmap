"""
Metrics collector — periodic aggregation of gateway metrics.
"""

from __future__ import annotations

import asyncio
import logging

from app.domain.ports.metrics_repository import MetricsRepositoryPort
from app.domain.ports.slot_repository import SlotRepositoryPort
from app.domain.ports.system_probe import SystemProbePort
from app.domain.ports.trace_repository import TraceRepositoryPort

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(
        self,
        metrics_repo: MetricsRepositoryPort,
        slot_repo: SlotRepositoryPort,
        trace_repo: TraceRepositoryPort,
        system_probe: SystemProbePort,
        collection_interval_sec: float = 10.0,
    ):
        self.metrics_repo = metrics_repo
        self.slot_repo = slot_repo
        self.trace_repo = trace_repo
        self.system_probe = system_probe
        self.collection_interval_sec = collection_interval_sec
        self._running = False
        self._task: asyncio.Task | None = None
        self._latest_snapshot: dict = {}

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Metrics collector started (interval=%.1fs)", self.collection_interval_sec)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Metrics collector stopped")

    async def _run(self):
        while self._running:
            try:
                slots = await self.slot_repo.get_all_slots()
                system = await self.system_probe.get_system_snapshot()
                trace_stats = await self.trace_repo.get_summary_stats()
                counters = await self.metrics_repo.get_snapshot()
                ttft_avg = await self.metrics_repo.get_ttft_avg()
                tps_avg = await self.metrics_repo.get_tokens_per_second_avg()

                self._latest_snapshot = {
                    "active_slots": sum(1 for s in slots if s.status.value == "busy"),
                    "idle_slots": sum(1 for s in slots if s.status.value == "idle"),
                    "total_slots": len(slots),
                    "memory_pressure": system.get("memory_pressure", 0.0),
                    "available_memory_mb": system.get("available_memory_mb", 0),
                    "cpu_usage_percent": system.get("cpu_usage_percent", 0.0),
                    "avg_ttft_ms": ttft_avg,
                    "avg_tokens_per_sec": tps_avg,
                    "counters": counters.get("counters", {}),
                    "trace_stats": trace_stats,
                }
            except Exception as e:
                logger.error("Metrics collection error: %s", e)
            await asyncio.sleep(self.collection_interval_sec)

    def get_snapshot(self) -> dict:
        return self._latest_snapshot
