"""
Token budget for a single request — estimates KV cache pressure.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenBudget:
    prompt_tokens: int = 0
    max_new_tokens: int = 2048
    estimated_kv_bytes: float = 0.0

    def __post_init__(self):
        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if self.max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be positive")

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.max_new_tokens