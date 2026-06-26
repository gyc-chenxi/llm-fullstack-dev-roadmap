"""
Long context planner — handles prompts exceeding the model's context window.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LongContextStrategy(str, Enum):
    PASS_THROUGH = "pass_through"
    COMPRESS = "compress"
    SLICE = "slice"
    RETRIEVE = "retrieve"


@dataclass
class LongContextPlanner:
    max_context_tokens: int = 8192
    low_threshold_ratio: float = 0.6

    def plan(self, prompt_tokens: int) -> LongContextStrategy:
        if prompt_tokens <= self.low_threshold_ratio * self.max_context_tokens:
            return LongContextStrategy.PASS_THROUGH
        if prompt_tokens <= self.max_context_tokens:
            return LongContextStrategy.COMPRESS
        return LongContextStrategy.RETRIEVE