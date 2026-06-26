"""
Priority value object for ordering requests in the queue.
Lower value = higher priority. Range: 1 (critical) to 10 (best-effort).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(order=True, frozen=True)
class Priority:
    value: int = 5

    def __post_init__(self):
        if not 1 <= self.value <= 10:
            raise ValueError(f"Priority must be between 1 and 10, got {self.value}")

    @staticmethod
    def critical() -> Priority:
        return Priority(1)

    @staticmethod
    def high() -> Priority:
        return Priority(3)

    @staticmethod
    def normal() -> Priority:
        return Priority(5)

    @staticmethod
    def low() -> Priority:
        return Priority(8)

    @staticmethod
    def best_effort() -> Priority:
        return Priority(10)