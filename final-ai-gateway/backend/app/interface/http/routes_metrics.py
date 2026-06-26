"""
Metrics Routes — GET /api/v1/metrics/snapshot, GET /api/v1/metrics/live
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from starlette.responses import JSONResponse

from app.application.orchestrators.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


def get_metrics_collector(request: Request) -> MetricsCollector:
    return request.app.state.metrics_collector


@router.get("/snapshot")
async def metrics_snapshot(
    collector: MetricsCollector = Depends(get_metrics_collector),
):
    """Get a snapshot of current gateway metrics."""
    return collector.get_snapshot()


@router.get("/live")
async def metrics_live(
    collector: MetricsCollector = Depends(get_metrics_collector),
):
    """Server-Sent Events stream of live metrics."""
    import asyncio

    async def _stream():
        while True:
            snapshot = collector.get_snapshot()
            import json
            yield f"data: {json.dumps(snapshot)}\n\n"
            await asyncio.sleep(2)

    from starlette.responses import StreamingResponse
    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
