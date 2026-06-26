"""
Prefix hash computed from a stable prompt prefix for cache matching.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class PrefixHash:
    hash_value: str
    prefix_tokens: int = 0

    @staticmethod
    def compute(prefix_text: str) -> PrefixHash:
        normalized = prefix_text.strip()
        h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return PrefixHash(hash_value=h, prefix_tokens=0)

    @staticmethod
    def compute_with_tokens(prefix_text: str, token_count: int) -> PrefixHash:
        normalized = prefix_text.strip()
        h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return PrefixHash(hash_value=h, prefix_tokens=token_count)