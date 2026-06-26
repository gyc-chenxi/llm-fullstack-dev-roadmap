"""
System Probe port — abstract interface for system resource monitoring.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class SystemProbePort(ABC):
    @abstractmethod
    async def get_memory_pressure(self) -> float:
        ...

    @abstractmethod
    async def get_available_memory_mb(self) -> int:
        ...

    @abstractmethod
    async def get_cpu_usage_percent(self) -> float:
        ...

    @abstractmethod
    async def get_system_snapshot(self) -> dict:
        ...
