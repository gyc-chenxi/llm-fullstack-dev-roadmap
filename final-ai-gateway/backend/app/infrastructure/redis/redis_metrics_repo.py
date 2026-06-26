"""
Redis-based metrics repository.
Stores metrics in Redis hashes with time-bucketed keys.
"""

from __future__ import annotations

import time
from typing import Any

from app.domain.ports.metrics_repository import MetricsRepositoryPort
from .connection import get_redis

METRICS_PREFIX = "gateway:metrics:"
LATENCY_KEY = f"{METRICS_PREFIX}latency"
COUNTER_KEY = f"{METRICS_PREFIX}counters"


class RedisMetricsRepo(MetricsRepositoryPort):
    async def record_latency(self, request_id: str, metric: str, value: float) -> None:
        r = get_redis()
        ts = int(time.time())
        key = f"{METRICS_PREFIX}latency:{metric}:{request_id}"
        await r.hset(key, mapping={"value": str(value), "ts": str(ts)})
        await r.expire(key, 3600)

    async def record_counter(self, metric: str, value: int = 1) -> None:
        r = get_redis()
        await r.hincrby(COUNTER_KEY, metric, value)

    async def get_snapshot(self) -> dict[str, Any]:
        r = get_redis()
        counters = await r.hgetall(COUNTER_KEY)
        return {
            "counters": {k: int(v) for k, v in counters.items()},
        }

    async def get_ttft_avg(self, window_sec: int = 60) -> float:
        r = get_redis()
        keys = await r.keys(f"{METRICS_PREFIX}latency:ttft_ms:*")
        if not keys:
            return 0.0
        total = 0.0
        count = 0
        now = int(time.time())
        for key in keys:
            data = await r.hgetall(key)
            ts = int(data.get("ts", 0))
            if now - ts <= window_sec:
                total += float(data.get("value", 0))
                count += 1
        return total / count if count > 0 else 0.0

    async def get_tokens_per_second_avg(self, window_sec: int = 60) -> float:
        r = get_redis()
        keys = await r.keys(f"{METRICS_PREFIX}latency:tokens_per_sec:*")
        if not keys:
            return 0.0
        total = 0.0
        count = 0
        now = int(time.time())
        for key in keys:
            data = await r.hgetall(key)
            ts = int(data.get("ts", 0))
            if now - ts <= window_sec:
                total += float(data.get("value", 0))
                count += 1
        return total / count if count > 0 else 0.0
