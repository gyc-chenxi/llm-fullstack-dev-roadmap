"""
Metrics Repository port — abstract interface for metrics storage and retrieval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MetricsRepositoryPort(ABC):
    @abstractmethod
    async def record_latency(self, request_id: str, metric: str, value: float) -> None:
        ...

    @abstractmethod
    async def record_counter(self, metric: str, value: int = 1) -> None:
        ...

    @abstractmethod
    async def get_snapshot(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_ttft_avg(self, window_sec: int = 60) -> float:
        ...

    @abstractmethod
    async def get_tokens_per_second_avg(self, window_sec: int = 60) -> float:
        ...
