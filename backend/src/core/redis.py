"""Redis connection utilities."""
from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis

# Redis client with string responses (decode_responses=True)
_redis_client: Redis[str] | None = None


async def get_redis(redis_url: str) -> Redis[Any]:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
