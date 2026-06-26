"""
Redis-based priority queue repository.
Uses sorted sets for priority ordering with FCFS tie-breaking.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Optional

from app.domain.entities.queue_ticket import QueueTicket
from app.domain.ports.queue_repository import QueueRepositoryPort
from .connection import get_redis

QUEUE_KEY = "gateway:queue:tickets"
QUEUE_SET_KEY = "gateway:queue:pending"


class RedisQueueRepository(QueueRepositoryPort):
    async def enqueue(self, ticket: QueueTicket) -> None:
        r = get_redis()
        score = ticket.priority * 1e15 + time.time() * 1e6
        data = json.dumps({
            "ticket_id": ticket.ticket_id,
            "request_id": ticket.request_id,
            "run_id": ticket.run_id,
            "priority": ticket.priority,
            "enqueued_at": ticket.enqueued_at.isoformat(),
            "attempts": ticket.attempts,
            "max_attempts": ticket.max_attempts,
        })
        await r.zadd(QUEUE_KEY, {data: score})

    async def dequeue(self) -> Optional[QueueTicket]:
        r = get_redis()
        results = await r.zpopmin(QUEUE_KEY, 1)
        if not results:
            return None
        raw, _ = results[0]
        data = json.loads(raw)
        from datetime import datetime

        return QueueTicket(
            ticket_id=data["ticket_id"],
            request_id=data["request_id"],
            run_id=data.get("run_id"),
            priority=data["priority"],
            enqueued_at=datetime.fromisoformat(data["enqueued_at"]),
            attempts=data.get("attempts", 0) + 1,
            max_attempts=data.get("max_attempts", 3),
        )

    async def peek(self) -> Optional[QueueTicket]:
        r = get_redis()
        results = await r.zrange(QUEUE_KEY, 0, 0, withscores=False)
        if not results:
            return None
        data = json.loads(results[0])
        from datetime import datetime

        return QueueTicket(
            ticket_id=data["ticket_id"],
            request_id=data["request_id"],
            priority=data["priority"],
            enqueued_at=datetime.fromisoformat(data["enqueued_at"]),
        )

    async def remove(self, request_id: str) -> bool:
        r = get_redis()
        results = await r.zrange(QUEUE_KEY, 0, -1, withscores=False)
        for raw in results:
            data = json.loads(raw)
            if data.get("request_id") == request_id:
                await r.zrem(QUEUE_KEY, raw)
                return True
        return False

    async def size(self) -> int:
        r = get_redis()
        return await r.zcard(QUEUE_KEY)
