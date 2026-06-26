"""
Redis Checkpointer — LangGraph-compatible checkpoint storage in Redis.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.infrastructure.redis.connection import get_redis

logger = logging.getLogger(__name__)

CHECKPOINT_PREFIX = "gateway:checkpoint:"


class RedisCheckpointer:
    def __init__(self):
        pass

    async def save(self, run_id: str, node_name: str, state: dict[str, Any],
                    event_id: int = 0) -> None:
        r = get_redis()
        key = f"{CHECKPOINT_PREFIX}{run_id}:{node_name}"
        import time
        data = {
            "run_id": run_id,
            "node_name": node_name,
            "state": json.dumps(state, default=str),
            "event_id": str(event_id),
            "created_at": str(time.time()),
        }
        await r.hset(key, mapping=data)
        await r.hset(f"{CHECKPOINT_PREFIX}{run_id}:latest", mapping={
            "node_name": node_name,
            "event_id": str(event_id),
        })

    async def load(self, run_id: str, node_name: str) -> Optional[dict[str, Any]]:
        r = get_redis()
        key = f"{CHECKPOINT_PREFIX}{run_id}:{node_name}"
        data = await r.hgetall(key)
        if not data:
            return None
        return {
            "run_id": data.get("run_id", ""),
            "node_name": data.get("node_name", ""),
            "state": json.loads(data.get("state", "{}")),
            "event_id": int(data.get("event_id", "0")),
            "created_at": data.get("created_at", ""),
        }

    async def get_latest_node(self, run_id: str) -> Optional[str]:
        r = get_redis()
        data = await r.hgetall(f"{CHECKPOINT_PREFIX}{run_id}:latest")
        return data.get("node_name") if data else None

    async def delete(self, run_id: str) -> None:
        r = get_redis()
        keys = await r.keys(f"{CHECKPOINT_PREFIX}{run_id}*")
        if keys:
            await r.delete(*keys)