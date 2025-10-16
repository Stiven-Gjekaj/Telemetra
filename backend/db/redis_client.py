"""
Redis client for caching and real-time data.
"""
import json
import redis.asyncio as aioredis
import structlog
from typing import Optional, Any
from datetime import datetime

from backend.config import settings

logger = structlog.get_logger(__name__)

# Global Redis client
_redis_client: Optional[aioredis.Redis] = None


async def init_redis_client() -> aioredis.Redis:
    """
    Initialize Redis client connection.

    Returns:
        aioredis.Redis: Initialized Redis client

    Raises:
        Exception: If connection cannot be established
    """
    global _redis_client

    if _redis_client is not None:
        logger.warning("Redis client already initialized")
        return _redis_client

    try:
        logger.info(
            "Initializing Redis client",
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
        )

        _redis_client = await aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )

        # Test connection
        await _redis_client.ping()

        logger.info("Redis client initialized successfully")
        return _redis_client

    except Exception as e:
        logger.error("Failed to initialize Redis client", error=str(e))
        raise


async def close_redis_client() -> None:
    """Close Redis client connection."""
    global _redis_client

    if _redis_client is None:
        logger.warning("Redis client not initialized")
        return

    try:
        logger.info("Closing Redis client")
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed successfully")
    except Exception as e:
        logger.error("Error closing Redis client", error=str(e))
        raise


def get_redis_client() -> aioredis.Redis:
    """
    Get the current Redis client.

    Returns:
        aioredis.Redis: Active Redis client

    Raises:
        RuntimeError: If client is not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis_client() first.")
    return _redis_client


async def check_redis_health() -> bool:
    """
    Check Redis connectivity.

    Returns:
        bool: True if Redis is accessible, False otherwise
    """
    try:
        client = get_redis_client()
        await client.ping()
        return True
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        return False


# Cache key builders

def _metrics_key(stream_id: str) -> str:
    """Build cache key for stream metrics."""
    return f"metrics:{stream_id}"


def _viewer_count_key(stream_id: str) -> str:
    """Build cache key for viewer count."""
    return f"viewer_count:{stream_id}"


def _chat_rate_key(stream_id: str) -> str:
    """Build cache key for chat rate."""
    return f"chat_rate:{stream_id}"


def _streams_key() -> str:
    """Build cache key for streams list."""
    return "streams:list"


# Caching operations

async def cache_latest_metrics(
    stream_id: str,
    viewer_count: int,
    chat_rate: float,
    unique_chatters: Optional[int] = None,
    top_emotes: Optional[list] = None,
    sentiment_score: Optional[float] = None,
) -> bool:
    """
    Cache latest metrics for a stream.

    Args:
        stream_id: Stream identifier
        viewer_count: Current viewer count
        chat_rate: Messages per minute
        unique_chatters: Number of unique chatters
        top_emotes: List of top emotes
        sentiment_score: Sentiment score

    Returns:
        bool: True if cached successfully
    """
    try:
        client = get_redis_client()

        metrics_data = {
            "stream_id": stream_id,
            "timestamp": datetime.utcnow().isoformat(),
            "viewer_count": viewer_count,
            "chat_rate": chat_rate,
            "unique_chatters": unique_chatters,
            "top_emotes": top_emotes or [],
            "sentiment_score": sentiment_score,
        }

        # Cache complete metrics object
        await client.setex(
            _metrics_key(stream_id),
            settings.cache_ttl_metrics,
            json.dumps(metrics_data),
        )

        # Also cache individual metrics for quick access
        await client.setex(
            _viewer_count_key(stream_id),
            settings.cache_ttl_metrics,
            str(viewer_count),
        )

        await client.setex(
            _chat_rate_key(stream_id),
            settings.cache_ttl_metrics,
            str(chat_rate),
        )

        logger.debug("Cached metrics", stream_id=stream_id)
        return True

    except Exception as e:
        logger.error("Error caching metrics", stream_id=stream_id, error=str(e))
        return False


async def get_cached_metrics(stream_id: str) -> Optional[dict]:
    """
    Get cached metrics for a stream.

    Args:
        stream_id: Stream identifier

    Returns:
        Dictionary with cached metrics or None if not found
    """
    try:
        client = get_redis_client()
        cached = await client.get(_metrics_key(stream_id))

        if cached:
            return json.loads(cached)
        return None

    except Exception as e:
        logger.error("Error getting cached metrics", stream_id=stream_id, error=str(e))
        return None


async def get_cached_viewer_count(stream_id: str) -> Optional[int]:
    """
    Get cached viewer count for a stream.

    Args:
        stream_id: Stream identifier

    Returns:
        Viewer count or None if not cached
    """
    try:
        client = get_redis_client()
        cached = await client.get(_viewer_count_key(stream_id))
        return int(cached) if cached else None
    except Exception as e:
        logger.error("Error getting cached viewer count", stream_id=stream_id, error=str(e))
        return None


async def get_cached_chat_rate(stream_id: str) -> Optional[float]:
    """
    Get cached chat rate for a stream.

    Args:
        stream_id: Stream identifier

    Returns:
        Chat rate or None if not cached
    """
    try:
        client = get_redis_client()
        cached = await client.get(_chat_rate_key(stream_id))
        return float(cached) if cached else None
    except Exception as e:
        logger.error("Error getting cached chat rate", stream_id=stream_id, error=str(e))
        return None


async def cache_streams_list(streams: list[dict]) -> bool:
    """
    Cache list of active streams.

    Args:
        streams: List of stream dictionaries

    Returns:
        bool: True if cached successfully
    """
    try:
        client = get_redis_client()
        await client.setex(
            _streams_key(),
            settings.cache_ttl_streams,
            json.dumps(streams),
        )
        logger.debug("Cached streams list", count=len(streams))
        return True
    except Exception as e:
        logger.error("Error caching streams list", error=str(e))
        return False


async def get_cached_streams_list() -> Optional[list[dict]]:
    """
    Get cached list of active streams.

    Returns:
        List of stream dictionaries or None if not cached
    """
    try:
        client = get_redis_client()
        cached = await client.get(_streams_key())
        return json.loads(cached) if cached else None
    except Exception as e:
        logger.error("Error getting cached streams list", error=str(e))
        return None


async def invalidate_cache(pattern: str = "*") -> int:
    """
    Invalidate cache entries matching a pattern.

    Args:
        pattern: Redis key pattern (default: all keys)

    Returns:
        Number of keys deleted
    """
    try:
        client = get_redis_client()
        keys = await client.keys(pattern)
        if keys:
            deleted = await client.delete(*keys)
            logger.info("Invalidated cache", pattern=pattern, deleted=deleted)
            return deleted
        return 0
    except Exception as e:
        logger.error("Error invalidating cache", pattern=pattern, error=str(e))
        return 0
