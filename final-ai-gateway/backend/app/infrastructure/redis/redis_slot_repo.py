"""
Redis-based slot state repository.
"""

from __future__ import annotations

import json
from typing import Optional

from app.domain.entities.slot import Slot, SlotStatus
from app.domain.ports.slot_repository import SlotRepositoryPort
from .connection import get_redis

SLOTS_KEY = "gateway:slots"


class RedisSlotRepo(SlotRepositoryPort):
    async def get_slot(self, slot_id: int) -> Optional[Slot]:
        r = get_redis()
        raw = await r.hget(SLOTS_KEY, str(slot_id))
        if not raw:
            return None
        return self._deserialize(raw)

    async def get_all_slots(self) -> list[Slot]:
        r = get_redis()
        raw = await r.hgetall(SLOTS_KEY)
        return [self._deserialize(v) for v in raw.values()]

    async def update_slot(self, slot: Slot) -> None:
        r = get_redis()
        await r.hset(SLOTS_KEY, str(slot.slot_id), self._serialize(slot))

    async def allocate_slot(self, slot_id: int, request_id: str) -> bool:
        r = get_redis()
        raw = await r.hget(SLOTS_KEY, str(slot_id))
        if not raw:
            return False
        slot = self._deserialize(raw)
        if slot.status != SlotStatus.IDLE:
            return False
        slot.status = SlotStatus.BUSY
        slot.current_request_id = request_id
        await r.hset(SLOTS_KEY, str(slot_id), self._serialize(slot))
        return True

    async def release_slot(self, slot_id: int) -> bool:
        r = get_redis()
        raw = await r.hget(SLOTS_KEY, str(slot_id))
        if not raw:
            return False
        slot = self._deserialize(raw)
        slot.status = SlotStatus.IDLE
        slot.current_request_id = None
        await r.hset(SLOTS_KEY, str(slot_id), self._serialize(slot))
        return True

    async def init_slots(self, count: int) -> None:
        r = get_redis()
        for i in range(count):
            slot = Slot(slot_id=i)
            await r.hset(SLOTS_KEY, str(i), self._serialize(slot))

    @staticmethod
    def _serialize(slot: Slot) -> str:
        return json.dumps({
            "slot_id": slot.slot_id,
            "status": slot.status.value,
            "current_request_id": slot.current_request_id or "",
            "prompt_tokens": slot.prompt_tokens,
            "tokens_generated": slot.tokens_generated,
            "prefix_hash": slot.prefix_hash or "",
            "cached_prompt_tokens": slot.cached_prompt_tokens,
        })

    @staticmethod
    def _deserialize(raw: str) -> Slot:
        data = json.loads(raw)
        return Slot(
            slot_id=data["slot_id"],
            status=SlotStatus(data["status"]),
            current_request_id=data.get("current_request_id") or None,
            prompt_tokens=data.get("prompt_tokens", 0),
            tokens_generated=data.get("tokens_generated", 0),
            prefix_hash=data.get("prefix_hash") or None,
            cached_prompt_tokens=data.get("cached_prompt_tokens", 0),
        )
