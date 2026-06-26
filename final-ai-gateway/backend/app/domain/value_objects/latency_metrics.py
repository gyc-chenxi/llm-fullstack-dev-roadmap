"""
Latency metrics value object capturing TTFT, TPOT, and total latency.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LatencyMetrics:
    ttft_ms: float = 0.0
    tpot_ms: float = 0.0
    total_latency_ms: float = 0.0
    queue_wait_ms: float = 0.0
    prefill_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    tokens_per_second: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def effective_latency_ms(self) -> float:
        return self.total_latency_ms + self.queue_wait_ms