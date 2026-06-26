"""
Slot Repository port — abstract interface for slot state persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from ..entities.slot import Slot


class SlotRepositoryPort(ABC):
    @abstractmethod
    async def get_slot(self, slot_id: int) -> Optional[Slot]:
        ...

    @abstractmethod
    async def get_all_slots(self) -> list[Slot]:
        ...

    @abstractmethod
    async def update_slot(self, slot: Slot) -> None:
        ...

    @abstractmethod
    async def allocate_slot(self, slot_id: int, request_id: str) -> bool:
        ...

    @abstractmethod
    async def release_slot(self, slot_id: int) -> bool:
        ...
