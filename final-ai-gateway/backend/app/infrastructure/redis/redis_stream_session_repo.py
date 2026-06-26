"""
Redis Stream-based SSE session repository.
Each stream session is stored as a Redis Stream with event_id-based ordering.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis

from app.domain.entities.stream_session import StreamSession, StreamStatus
from .connection import get_redis

STREAM_PREFIX = "gateway:stream:"
SESSION_KEY_PREFIX = "gateway:session:"


class RedisStreamSessionRepo:
    def __init__(self):
        pass

    def _stream_key(self, request_id: str) -> str:
        return f"{STREAM_PREFIX}{request_id}"

    def _session_key(self, request_id: str) -> str:
        return f"{SESSION_KEY_PREFIX}{request_id}"

    async def create_session(self, session: StreamSession) -> None:
        r = get_redis()
        data = {
            "session_id": session.session_id,
            "request_id": session.request_id,
            "run_id": session.run_id or "",
            "stream_type": session.stream_type,
            "last_event_id": str(session.last_event_id),
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
        }
        await r.hset(self._session_key(session.request_id), mapping=data)

    async def add_event(self, request_id: str, event_data: dict) -> int:
        r = get_redis()
        current = await r.hget(self._session_key(request_id), "last_event_id")
        event_id = (int(current) + 1) if current else 1
        payload = json.dumps({"event_id": event_id, **event_data})
        await r.xadd(self._stream_key(request_id), {"data": payload}, maxlen=10000)
        await r.hset(self._session_key(request_id), "last_event_id", str(event_id))
        return event_id

    async def get_events_since(self, request_id: str, last_event_id: int = 0,
                                count: int = 100) -> list[dict]:
        r = get_redis()
        stream_key = self._stream_key(request_id)
        try:
            results = await r.xrange(stream_key, min=f"{int(last_event_id) + 1}-0", count=count)
        except aioredis.ResponseError:
            return []
        events = []
        for msg_id, fields in results:
            raw = fields.get(b"data", fields.get("data", "{}"))
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            events.append(json.loads(raw))
        return events

    async def get_session(self, request_id: str) -> Optional[StreamSession]:
        r = get_redis()
        data = await r.hgetall(self._session_key(request_id))
        if not data:
            return None
        return StreamSession(
            session_id=data.get("session_id", ""),
            request_id=data.get("request_id", ""),
            run_id=data.get("run_id") or None,
            stream_type=data.get("stream_type", "chat"),
            last_event_id=int(data.get("last_event_id", "0")),
            status=StreamStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
        )

    async def update_status(self, request_id: str, status: StreamStatus,
                             error_message: Optional[str] = None) -> None:
        r = get_redis()
        mapping = {"status": status.value}
        if error_message:
            mapping["error_message"] = error_message
        await r.hset(self._session_key(request_id), mapping=mapping)

    async def store_messages(self, request_id: str, messages: list[dict],
                              model: str = "", max_tokens: int = 2048,
                              temperature: float = 0.7) -> None:
        r = get_redis()
        data = json.dumps({
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })
        await r.hset(self._session_key(request_id), "params", data)

    async def get_messages(self, request_id: str) -> Optional[dict]:
        r = get_redis()
        raw = await r.hget(self._session_key(request_id), "params")
        if not raw:
            return None
        return json.loads(raw)
