"""
Redis connection pool — singleton-style async Redis client provider.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator, Optional

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool

logger = logging.getLogger(__name__)

_pool: Optional[ConnectionPool] = None


async def init_redis_pool(redis_url: str = "redis://localhost:6379/0", max_connections: int = 50) -> ConnectionPool:
    global _pool
    _pool = aioredis.ConnectionPool.from_url(
        redis_url,
        max_connections=max_connections,
        decode_responses=True,
        socket_keepalive=True,
        socket_connect_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30,
    )
    client = aioredis.Redis(connection_pool=_pool)
    await client.ping()
    logger.info("Redis connection pool initialized: %s (max=%d)", redis_url, max_connections)
    await client.close()
    return _pool


async def close_redis_pool():
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        logger.info("Redis connection pool closed")
        _pool = None


def get_redis() -> aioredis.Redis:
    if _pool is None:
        raise RuntimeError("Redis pool not initialized — call init_redis_pool() first")
    return aioredis.Redis(connection_pool=_pool)


async def get_redis_async() -> AsyncIterator[aioredis.Redis]:
    client = get_redis()
    try:
        yield client
    finally:
        await client.aclose()
