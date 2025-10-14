"""
Redis caching utilities for Telemetra backend.

Provides helper functions for cache-aside pattern with TTL support.
"""

import json
from typing import Optional, Any, Callable
from redis.asyncio import Redis


async def get_cached(redis_client: Redis, key: str) -> Optional[Any]:
    """
    Retrieve a value from cache.

    Args:
        redis_client: Redis client instance
        key: Cache key

    Returns:
        Cached value (parsed from JSON) or None if not found
    """
    try:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Cache get error for key '{key}': {e}")
        return None


async def set_cached(redis_client: Redis, key: str, value: Any, ttl: int) -> bool:
    """
    Store a value in cache with TTL.

    Args:
        redis_client: Redis client instance
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        serialized = json.dumps(value)
        await redis_client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        print(f"Cache set error for key '{key}': {e}")
        return False


async def delete_cached(redis_client: Redis, key: str) -> bool:
    """
    Delete a value from cache.

    Args:
        redis_client: Redis client instance
        key: Cache key

    Returns:
        True if successful, False otherwise
    """
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error for key '{key}': {e}")
        return False


async def get_or_set(
    redis_client: Redis,
    key: str,
    factory_func: Callable,
    ttl: int
) -> Any:
    """
    Cache-aside pattern: Get from cache or execute factory function and cache result.

    Args:
        redis_client: Redis client instance
        key: Cache key
        factory_func: Async function to execute on cache miss
        ttl: Time to live in seconds

    Returns:
        Cached or freshly computed value
    """
    # Try to get from cache
    cached = await get_cached(redis_client, key)
    if cached is not None:
        return cached

    # Cache miss - execute factory function
    result = await factory_func()

    # Store in cache
    await set_cached(redis_client, key, result, ttl)

    return result


# Cache key patterns
def stream_list_key() -> str:
    """Key for cached stream list."""
    return "streams:list"


def stream_latest_chat_key(stream_id: str) -> str:
    """Key for latest chat metrics of a stream."""
    return f"stream:{stream_id}:latest:chat"


def stream_latest_viewer_key(stream_id: str) -> str:
    """Key for latest viewer metrics of a stream."""
    return f"stream:{stream_id}:latest:viewer"


def stream_metrics_key(stream_id: str, minutes: int) -> str:
    """Key for historical metrics with time window."""
    return f"stream:{stream_id}:metrics:{minutes}"
