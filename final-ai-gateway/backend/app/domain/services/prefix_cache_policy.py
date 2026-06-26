"""
Prefix cache policy — decides whether a prefix should be cached and on which slot.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..value_objects.prefix_hash import PrefixHash


@dataclass
class PrefixCachePolicy:
    min_prefix_tokens: int = 128
    cache_entries: dict[str, dict] = field(default_factory=dict)

    def should_cache(self, prefix_text: str) -> bool:
        return len(prefix_text.split()) >= self.min_prefix_tokens // 2

    def lookup(self, prefix_hash: str) -> Optional[dict]:
        return self.cache_entries.get(prefix_hash)

    def register(self, prefix_hash: str, slot_id: int, prefix_tokens: int):
        self.cache_entries[prefix_hash] = {
            "prefix_hash": prefix_hash,
            "slot_id": slot_id,
            "prefix_tokens": prefix_tokens,
        }