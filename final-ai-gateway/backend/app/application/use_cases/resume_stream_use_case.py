"""
Resume SSE stream use case — replays missed events from Redis Stream.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator

from app.domain.ports.trace_repository import TraceRepositoryPort
from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo
from app.infrastructure.sse.sse_event_store import SseEventStore, format_sse_event

logger = logging.getLogger(__name__)


class ResumeStreamUseCase:
    def __init__(
        self,
        stream_session_repo: RedisStreamSessionRepo,
        trace_repo: TraceRepositoryPort,
        sse_store: SseEventStore,
    ):
        self.stream_session_repo = stream_session_repo
        self.trace_repo = trace_repo
        self.sse_store = sse_store

    async def execute(self, request_id: str, last_event_id: int = 0) -> AsyncIterator[str]:
        events = await self.stream_session_repo.get_events_since(
            request_id, last_event_id, count=500
        )

        if not events:
            session = await self.stream_session_repo.get_session(request_id)
            if session is None:
                yield format_sse_event(0, request_id, "error",
                                        {"message": "session not found"})
                return
            if session.status.value == "done":
                yield format_sse_event(0, request_id, "done",
                                        {"message": "stream already completed"})
                return

        for evt in events:
            eid = evt.get("event_id", 0)
            etype = evt.get("type", "unknown")
            yield format_sse_event(eid, request_id, etype, evt)

        session = await self.stream_session_repo.get_session(request_id)
        if session and session.status.value == "done":
            yield format_sse_event(
                events[-1]["event_id"] + 1 if events else 1,
                request_id,
                "done",
                {"source": "replay_complete"},
            )