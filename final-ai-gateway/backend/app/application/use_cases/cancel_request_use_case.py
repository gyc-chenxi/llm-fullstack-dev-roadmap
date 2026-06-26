"""
Cancel request use case — cancels a queued or streaming request.
"""

from __future__ import annotations

import logging

from app.domain.entities.stream_session import StreamStatus
from app.domain.ports.queue_repository import QueueRepositoryPort
from app.domain.ports.slot_repository import SlotRepositoryPort
from app.domain.ports.trace_repository import TraceRepositoryPort
from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo

logger = logging.getLogger(__name__)


class CancelRequestUseCase:
    def __init__(
        self,
        queue_repo: QueueRepositoryPort,
        slot_repo: SlotRepositoryPort,
        trace_repo: TraceRepositoryPort,
        stream_session_repo: RedisStreamSessionRepo,
    ):
        self.queue_repo = queue_repo
        self.slot_repo = slot_repo
        self.trace_repo = trace_repo
        self.stream_session_repo = stream_session_repo

    async def execute(self, request_id: str) -> dict:
        session = await self.stream_session_repo.get_session(request_id)
        if session and session.status == StreamStatus.ACTIVE:
            await self.stream_session_repo.update_status(request_id, StreamStatus.CANCELLED)
            return {"request_id": request_id, "status": "cancelled", "from": "streaming"}

        removed = await self.queue_repo.remove(request_id)
        if removed:
            return {"request_id": request_id, "status": "cancelled", "from": "queue"}

        return {"request_id": request_id, "status": "not_found"}