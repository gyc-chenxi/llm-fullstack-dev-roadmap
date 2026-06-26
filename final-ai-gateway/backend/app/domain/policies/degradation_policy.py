"""
Degradation policy — determines fallback behavior when the system is under stress.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DegradationLevel(str, Enum):
    NONE = "none"
    LIGHT = "light"
    MODERATE = "moderate"
    SEVERE = "severe"


@dataclass
class DegradationPolicy:
    light_queue_threshold: int = 5
    moderate_queue_threshold: int = 20
    severe_queue_threshold: int = 50
    light_kv_ratio: float = 0.85
    moderate_kv_ratio: float = 0.95
    severe_kv_ratio: float = 0.99

    def evaluate(self, queue_depth: int, kv_usage_ratio: float) -> DegradationLevel:
        if queue_depth >= self.severe_queue_threshold or kv_usage_ratio >= self.severe_kv_ratio:
            return DegradationLevel.SEVERE
        if queue_depth >= self.moderate_queue_threshold or kv_usage_ratio >= self.moderate_kv_ratio:
            return DegradationLevel.MODERATE
        if queue_depth >= self.light_queue_threshold or kv_usage_ratio >= self.light_kv_ratio:
            return DegradationLevel.LIGHT
        return DegradationLevel.NONE