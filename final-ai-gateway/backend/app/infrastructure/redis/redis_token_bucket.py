"""
Redis-based token bucket for per-tenant rate limiting.
Uses sliding window counters in Redis.
"""

from __future__ import annotations

import time
from typing import Optional

from app.domain.services.token_bucket_limiter import TokenBucketLimiter
from .connection import get_redis

BUCKET_PREFIX = "gateway:bucket:"


class RedisTokenBucket:
    def __init__(self):
        pass

    async def consume(self, tenant_id: str, rate: float, burst: int,
                       tokens: int = 1) -> bool:
        r = get_redis()
        key = f"{BUCKET_PREFIX}{tenant_id}"
        now = time.time()
        window = float(burst) / rate if rate > 0 else 1.0

        lua = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local burst = tonumber(ARGV[3])
        local tokens = tonumber(ARGV[4])

        redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
        local count = redis.call('ZCARD', key)

        if count + tokens <= burst then
            for i = 1, tokens do
                redis.call('ZADD', key, now + i * 0.001, now .. '-' .. i)
            end
            redis.call('EXPIRE', key, math.ceil(window) + 1)
            return 1
        end
        return 0
        """
        result = await r.eval(lua, 1, key, str(now), str(window), str(burst), str(tokens))
        return result == 1

    async def get_available(self, tenant_id: str, rate: float, burst: int) -> int:
        r = get_redis()
        key = f"{BUCKET_PREFIX}{tenant_id}"
        now = time.time()
        window = float(burst) / rate if rate > 0 else 1.0
        await r.zremrangebyscore(key, 0, now - window)
        used = await r.zcard(key)
        return max(0, burst - used)
