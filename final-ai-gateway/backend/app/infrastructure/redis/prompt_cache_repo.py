"""
Redis-based prompt cache repository.
"""

from __future__ import annotations

import json
import time
from typing import Optional

from app.domain.ports.prompt_cache_repository import PromptCacheRepositoryPort
from .connection import get_redis

CACHE_KEY = "gateway:prompt_cache"


class RedisPromptCacheRepo(PromptCacheRepositoryPort):
    async def get(self, prefix_hash: str) -> Optional[dict]:
        r = get_redis()
        raw = await r.hget(CACHE_KEY, prefix_hash)
        if not raw:
            return None
        return json.loads(raw)

    async def set(self, prefix_hash: str, slot_id: int, prefix_tokens: int) -> None:
        r = get_redis()
        data = json.dumps({
            "prefix_hash": prefix_hash,
            "slot_id": slot_id,
            "prefix_tokens": prefix_tokens,
            "last_used_at": time.time(),
            "hit_count": 1,
        })
        await r.hset(CACHE_KEY, prefix_hash, data)

    async def delete(self, prefix_hash: str) -> None:
        r = get_redis()
        await r.hdel(CACHE_KEY, prefix_hash)

    async def touch(self, prefix_hash: str) -> None:
        r = get_redis()
        raw = await r.hget(CACHE_KEY, prefix_hash)
        if raw:
            data = json.loads(raw)
            data["last_used_at"] = time.time()
            data["hit_count"] = data.get("hit_count", 0) + 1
            await r.hset(CACHE_KEY, prefix_hash, json.dumps(data))

    async def get_all(self) -> list[dict]:
        r = get_redis()
        raw = await r.hgetall(CACHE_KEY)
        return [json.loads(v) for v in raw.values()]
