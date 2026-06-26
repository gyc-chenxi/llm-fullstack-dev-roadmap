"""
Retry policy — determines whether and how to retry a failed request.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay_ms: int = 500
    max_delay_ms: int = 10000
    backoff_multiplier: float = 2.0

    def should_retry(self, attempt: int, error_type: str) -> bool:
        if attempt >= self.max_retries:
            return False
        if error_type in ("circuit_breaker_open", "over_max_tokens", "invalid_request"):
            return False
        return True

    def delay_ms(self, attempt: int) -> int:
        delay = self.base_delay_ms * (self.backoff_multiplier ** attempt)
        return min(int(delay), self.max_delay_ms)