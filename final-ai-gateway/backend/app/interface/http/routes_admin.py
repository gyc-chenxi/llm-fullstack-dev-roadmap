"""
Admin Routes — POST /api/v1/admin/health, POST /api/v1/admin/queue-info
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request

from app.application.orchestrators.metrics_collector import MetricsCollector
from app.domain.ports.queue_repository import QueueRepositoryPort
from app.infrastructure.redis.redis_priority_queue import RedisQueueRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def get_queue_repo(request: Request) -> QueueRepositoryPort:
    return request.app.state.queue_repo


def get_metrics_collector(request: Request) -> MetricsCollector:
    return request.app.state.metrics_collector


@router.get("/health")
async def health():
    """Gateway health check."""
    return {"status": "ok", "service": "ai-gateway"}


@router.get("/queue-info")
async def queue_info(
    queue_repo: QueueRepositoryPort = Depends(get_queue_repo),
):
    """Get current queue depth and status."""
    size = await queue_repo.size()
    peek = await queue_repo.peek()
    return {
        "queue_depth": size,
        "next_ticket": {
            "ticket_id": peek.ticket_id,
            "request_id": peek.request_id,
            "priority": peek.priority,
        } if peek else None,
    }
