"""
Metrics snapshot DTO.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MetricsSnapshotDTO(BaseModel):
    counters: dict[str, int] = {}
    avg_ttft_ms: float = 0.0
    avg_tokens_per_sec: float = 0.0
    active_slots: int = 0
    queue_depth: int = 0
    memory_pressure: float = 0.0
    trace_stats: dict[str, Any] = {}