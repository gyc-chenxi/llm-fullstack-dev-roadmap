"""
Trace Routes — GET /api/v1/trace/{trace_id}
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Query

from app.application.orchestrators.trace_collector import TraceCollector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/trace", tags=["trace"])


def get_trace_collector(request: Request) -> TraceCollector:
    return request.app.state.trace_collector


@router.get("/{trace_id}")
async def get_trace(
    trace_id: str,
    collector: TraceCollector = Depends(get_trace_collector),
):
    """Get a specific trace by ID."""
    trace = await collector.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return {
        "trace_id": trace.trace_id,
        "request_id": trace.request_id,
        "run_type": trace.run_type,
        "latency_ms": trace.latency_ms,
        "prompt_tokens": trace.prompt_tokens,
        "completion_tokens": trace.completion_tokens,
        "ttft_ms": trace.ttft_ms,
        "tpot_ms": trace.tpot_ms,
        "queue_wait_ms": trace.queue_wait_ms,
        "model_backend": trace.model_backend,
        "slot_id": trace.slot_id,
        "final_status": trace.final_status,
        "spans": trace.spans,
        "tool_calls": trace.tool_calls,
        "citations": trace.citations,
        "errors": trace.errors,
    }


@router.get("")
async def list_traces(
    run_type: str = Query(default=""),
    limit: int = Query(default=20, le=100),
    collector: TraceCollector = Depends(get_trace_collector),
):
    """List recent traces, optionally filtered by run_type."""
    traces = await collector.get_recent(run_type=run_type, limit=limit)
    return {
        "total": len(traces),
        "traces": [
            {
                "trace_id": t.trace_id,
                "request_id": t.request_id,
                "run_type": t.run_type,
                "ttft_ms": t.ttft_ms,
                "latency_ms": t.latency_ms,
                "final_status": t.final_status,
            }
            for t in traces
        ],
    }
