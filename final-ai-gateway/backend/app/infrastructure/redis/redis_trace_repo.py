"""
Redis-based trace repository.
Stores traces as JSON in Redis hashes.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from app.domain.entities.trace_run import TraceRun
from app.domain.ports.trace_repository import TraceRepositoryPort
from .connection import get_redis

TRACE_PREFIX = "gateway:trace:"
TRACE_LIST_KEY = "gateway:trace:recent"


class RedisTraceRepo(TraceRepositoryPort):
    async def save(self, trace: TraceRun) -> None:
        r = get_redis()
        data = {
            "trace_id": trace.trace_id,
            "request_id": trace.request_id,
            "run_type": trace.run_type,
            "latency_ms": str(trace.latency_ms),
            "prompt_tokens": str(trace.prompt_tokens),
            "completion_tokens": str(trace.completion_tokens),
            "ttft_ms": str(trace.ttft_ms),
            "tpot_ms": str(trace.tpot_ms),
            "queue_wait_ms": str(trace.queue_wait_ms),
            "model_backend": trace.model_backend,
            "slot_id": str(trace.slot_id) if trace.slot_id is not None else "",
            "final_status": trace.final_status,
            "created_at": trace.created_at.isoformat(),
            "errors": json.dumps(trace.errors),
            "spans": json.dumps(trace.spans),
            "tool_calls": json.dumps(trace.tool_calls),
            "citations": json.dumps(trace.citations),
        }
        key = f"{TRACE_PREFIX}{trace.trace_id}"
        await r.hset(key, mapping=data)
        await r.expire(key, 86400)
        await r.lpush(TRACE_LIST_KEY, trace.trace_id)
        await r.ltrim(TRACE_LIST_KEY, 0, 999)

    async def get(self, trace_id: str) -> Optional[TraceRun]:
        r = get_redis()
        data = await r.hgetall(f"{TRACE_PREFIX}{trace_id}")
        if not data:
            return None
        return self._deserialize(data)

    async def query_recent(self, run_type: str = "", limit: int = 20) -> list[TraceRun]:
        r = get_redis()
        ids = await r.lrange(TRACE_LIST_KEY, 0, limit - 1)
        traces = []
        for tid in ids:
            data = await r.hgetall(f"{TRACE_PREFIX}{tid}")
            if data:
                trace = self._deserialize(data)
                if not run_type or trace.run_type == run_type:
                    traces.append(trace)
        return traces

    async def get_summary_stats(self, window_sec: int = 3600) -> dict[str, Any]:
        traces = await self.query_recent(limit=100)
        if not traces:
            return {}
        ttfts = [t.ttft_ms for t in traces if t.ttft_ms > 0]
        latencies = [t.latency_ms for t in traces if t.latency_ms > 0]
        return {
            "total_traces": len(traces),
            "avg_ttft_ms": sum(ttfts) / len(ttfts) if ttfts else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "success_rate": sum(1 for t in traces if t.final_status == "completed") / len(traces),
        }

    @staticmethod
    def _deserialize(data: dict) -> TraceRun:
        from datetime import datetime

        return TraceRun(
            trace_id=data.get("trace_id", ""),
            request_id=data.get("request_id", ""),
            run_type=data.get("run_type", "chat"),
            latency_ms=float(data.get("latency_ms", 0)),
            prompt_tokens=int(data.get("prompt_tokens", 0)),
            completion_tokens=int(data.get("completion_tokens", 0)),
            ttft_ms=float(data.get("ttft_ms", 0)),
            tpot_ms=float(data.get("tpot_ms", 0)),
            queue_wait_ms=float(data.get("queue_wait_ms", 0)),
            model_backend=data.get("model_backend", ""),
            slot_id=int(data["slot_id"]) if data.get("slot_id") else None,
            final_status=data.get("final_status", "unknown"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
            errors=json.loads(data.get("errors", "[]")),
            spans=json.loads(data.get("spans", "[]")),
            tool_calls=json.loads(data.get("tool_calls", "[]")),
            citations=json.loads(data.get("citations", "[]")),
        )
