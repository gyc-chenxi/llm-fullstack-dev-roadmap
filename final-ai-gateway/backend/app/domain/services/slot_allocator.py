"""
Slot allocator — manages slot lifecycle for the local model backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ..entities.slot import Slot, SlotStatus


@dataclass
class SlotAllocator:
    slots: list[Slot] = field(default_factory=list)

    @classmethod
    def from_count(cls, count: int) -> SlotAllocator:
        return cls(slots=[Slot(slot_id=i) for i in range(count)])

    def allocate(self, request_id: str, prefix_hash: Optional[str] = None) -> Optional[Slot]:
        for slot in self.slots:
            if slot.status == SlotStatus.IDLE:
                slot.status = SlotStatus.BUSY
                slot.current_request_id = request_id
                slot.allocated_at = datetime.now(timezone.utc)
                slot.prefix_hash = prefix_hash
                return slot
        return None

    def release(self, slot_id: int):
        for slot in self.slots:
            if slot.slot_id == slot_id:
                slot.status = SlotStatus.IDLE
                slot.current_request_id = None
                slot.prompt_tokens = 0
                slot.tokens_generated = 0
                slot.allocated_at = None
                return

    def find_by_prefix(self, prefix_hash: str) -> Optional[Slot]:
        for slot in self.slots:
            if slot.prefix_hash == prefix_hash and slot.cached_prompt_tokens > 0:
                return slot
        return None

    @property
    def active_count(self) -> int:
        return sum(1 for s in self.slots if s.status == SlotStatus.BUSY)

    @property
    def idle_count(self) -> int:
        return sum(1 for s in self.slots if s.status == SlotStatus.IDLE)