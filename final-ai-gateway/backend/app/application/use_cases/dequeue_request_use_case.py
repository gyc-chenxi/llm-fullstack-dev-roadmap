"""
Dequeue request use case — pops from Redis priority queue and initiates admission.
"""

from __future__ import annotations

import logging

from app.domain.entities.stream_session import StreamSession
from app.domain.ports.queue_repository import QueueRepositoryPort
from app.domain.ports.slot_repository import SlotRepositoryPort
from app.domain.services.slot_allocator import SlotAllocator
from app.infrastructure.redis.redis_stream_session_repo import RedisStreamSessionRepo

logger = logging.getLogger(__name__)


class DequeueRequestUseCase:
    def __init__(
        self,
        queue_repo: QueueRepositoryPort,
        slot_allocator: SlotAllocator,
        slot_repo: SlotRepositoryPort,
        stream_session_repo: RedisStreamSessionRepo,
    ):
        self.queue_repo = queue_repo
        self.slot_allocator = slot_allocator
        self.slot_repo = slot_repo
        self.stream_session_repo = stream_session_repo

    async def execute(self) -> dict | None:
        ticket = await self.queue_repo.dequeue()
        if ticket is None:
            return None

        slot = self.slot_allocator.allocate(ticket.request_id)
        if slot is None:
            await self.queue_repo.enqueue(ticket)
            return None

        await self.slot_repo.allocate_slot(slot.slot_id, ticket.request_id)

        session = StreamSession(
            request_id=ticket.request_id,
            stream_type="chat",
        )
        await self.stream_session_repo.create_session(session)

        return {
            "request_id": ticket.request_id,
            "ticket_id": ticket.ticket_id,
            "slot_id": slot.slot_id,
            "status": "admitted_from_queue",
        }