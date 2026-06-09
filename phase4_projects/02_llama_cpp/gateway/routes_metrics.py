"""
Gateway-side metrics endpoint.

Why this exists (interview answer):
llama-server exposes its own /metrics (prompt tokens, predicted tokens,
slot utilization).  But the Gateway has its own concerns — request count,
error rate, upstream latency distribution.  These are *Gateway* metrics,
not model metrics.  In production you'd use prometheus-client counters
and histograms; here we do a lightweight in-process snapshot that a
Prometheus textfile collector or a simple curl poll could scrape.
"""

import time

from fastapi import APIRouter

router = APIRouter(tags=["observability"])

# In-process counters (reset on restart — acceptable for local dev).
_started_at = time.time()
_request_count = 0
_error_count = 0
_last_latency_ms: float = 0.0


def record_request(latency_ms: float, is_error: bool = False) -> None:
    """Called by routes to record metrics after each upstream call."""
    global _request_count, _error_count, _last_latency_ms
    _request_count += 1
    if is_error:
        _error_count += 1
    _last_latency_ms = latency_ms


@router.get("/gateway/metrics")
async def gateway_metrics():
    """Return a JSON snapshot of gateway-side metrics."""
    uptime = time.time() - _started_at
    return {
        "uptime_seconds": round(uptime, 1),
        "requests_total": _request_count,
        "errors_total": _error_count,
        "error_rate": round(_error_count / max(_request_count, 1), 4),
        "last_latency_ms": _last_latency_ms,
        "rate_limit_enabled": False,  # updated by app startup
    }
