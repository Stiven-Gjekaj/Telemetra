"""
Database connection management using asyncpg.
Implements connection pooling for efficient database access.
"""
import asyncpg
import structlog
from typing import Optional
from contextlib import asynccontextmanager

from backend.config import settings

logger = structlog.get_logger(__name__)

# Global connection pool
_db_pool: Optional[asyncpg.Pool] = None


async def init_db_pool() -> asyncpg.Pool:
    """
    Initialize the database connection pool.

    Returns:
        asyncpg.Pool: Initialized connection pool

    Raises:
        Exception: If connection cannot be established
    """
    global _db_pool

    if _db_pool is not None:
        logger.warning("Database pool already initialized")
        return _db_pool

    try:
        logger.info(
            "Initializing database connection pool",
            host=settings.postgres_host,
            port=settings.postgres_port,
            database=settings.postgres_db,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
        )

        _db_pool = await asyncpg.create_pool(
            host=settings.postgres_host,
            port=settings.postgres_port,
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            min_size=settings.db_pool_min_size,
            max_size=settings.db_pool_max_size,
            timeout=settings.db_pool_timeout,
            command_timeout=60,
        )

        logger.info("Database connection pool initialized successfully")
        return _db_pool

    except Exception as e:
        logger.error("Failed to initialize database pool", error=str(e))
        raise


async def close_db_pool() -> None:
    """Close the database connection pool."""
    global _db_pool

    if _db_pool is None:
        logger.warning("Database pool not initialized")
        return

    try:
        logger.info("Closing database connection pool")
        await _db_pool.close()
        _db_pool = None
        logger.info("Database connection pool closed successfully")
    except Exception as e:
        logger.error("Error closing database pool", error=str(e))
        raise


def get_db_pool() -> asyncpg.Pool:
    """
    Get the current database connection pool.

    Returns:
        asyncpg.Pool: Active connection pool

    Raises:
        RuntimeError: If pool is not initialized
    """
    if _db_pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db_pool() first.")
    return _db_pool


@asynccontextmanager
async def get_db_connection():
    """
    Context manager for acquiring a database connection from the pool.

    Usage:
        async with get_db_connection() as conn:
            result = await conn.fetch("SELECT * FROM streams")
    """
    pool = get_db_pool()
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await pool.release(conn)


async def check_db_health() -> bool:
    """
    Check database connectivity.

    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        pool = get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False


# Query helpers for common operations

async def get_streams(limit: int = 100, offset: int = 0) -> list[dict]:
    """
    Fetch all streams from the database.

    Args:
        limit: Maximum number of streams to return
        offset: Number of streams to skip

    Returns:
        List of stream records as dictionaries
    """
    query = """
        SELECT
            stream_id,
            streamer_name,
            title,
            game_category,
            started_at,
            is_live,
            COALESCE(
                (SELECT viewer_count
                 FROM viewer_timeseries
                 WHERE stream_id = s.stream_id
                 ORDER BY timestamp DESC
                 LIMIT 1),
                0
            ) as viewer_count
        FROM streams s
        WHERE is_live = true
        ORDER BY started_at DESC
        LIMIT $1 OFFSET $2
    """

    try:
        pool = get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, limit, offset)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Error fetching streams", error=str(e))
        raise


async def get_stream_metrics(stream_id: str, limit: int = 100) -> list[dict]:
    """
    Fetch metrics for a specific stream.

    Args:
        stream_id: Stream identifier
        limit: Maximum number of metric records to return

    Returns:
        List of metric records as dictionaries
    """
    query = """
        WITH latest_chat AS (
            SELECT
                timestamp,
                chat_count,
                unique_chatters,
                top_emotes,
                sentiment_score
            FROM chat_summary_minute
            WHERE stream_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        ),
        latest_viewers AS (
            SELECT
                timestamp,
                viewer_count
            FROM viewer_timeseries
            WHERE stream_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        )
        SELECT
            COALESCE(c.timestamp, v.timestamp) as timestamp,
            COALESCE(v.viewer_count, 0) as viewer_count,
            COALESCE(c.chat_count, 0) as chat_rate,
            COALESCE(c.unique_chatters, 0) as unique_chatters,
            COALESCE(c.top_emotes, '[]'::jsonb) as top_emotes,
            c.sentiment_score
        FROM latest_chat c
        FULL OUTER JOIN latest_viewers v
            ON c.timestamp = v.timestamp
        ORDER BY COALESCE(c.timestamp, v.timestamp) DESC
    """

    try:
        pool = get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, stream_id, limit)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Error fetching stream metrics", stream_id=stream_id, error=str(e))
        raise


async def get_stream_moments(stream_id: str, limit: int = 50) -> list[dict]:
    """
    Fetch detected moments/anomalies for a stream.

    Args:
        stream_id: Stream identifier
        limit: Maximum number of moments to return

    Returns:
        List of moment records as dictionaries
    """
    query = """
        SELECT
            moment_id,
            stream_id,
            timestamp,
            moment_type,
            description,
            metric_name,
            metric_value,
            threshold,
            z_score,
            metadata
        FROM moments
        WHERE stream_id = $1
        ORDER BY timestamp DESC
        LIMIT $2
    """

    try:
        pool = get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(query, stream_id, limit)
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error("Error fetching moments", stream_id=stream_id, error=str(e))
        raise


async def get_latest_metrics(stream_id: str) -> Optional[dict]:
    """
    Get the most recent metrics for a stream (for WebSocket updates).

    Args:
        stream_id: Stream identifier

    Returns:
        Dictionary with latest metrics or None if not found
    """
    query = """
        WITH latest_chat AS (
            SELECT
                timestamp,
                chat_count,
                unique_chatters,
                top_emotes,
                sentiment_score
            FROM chat_summary_minute
            WHERE stream_id = $1
            ORDER BY timestamp DESC
            LIMIT 1
        ),
        latest_viewer AS (
            SELECT
                timestamp,
                viewer_count
            FROM viewer_timeseries
            WHERE stream_id = $1
            ORDER BY timestamp DESC
            LIMIT 1
        )
        SELECT
            COALESCE(c.timestamp, v.timestamp) as timestamp,
            COALESCE(v.viewer_count, 0) as viewer_count,
            COALESCE(c.chat_count, 0) as chat_rate,
            COALESCE(c.unique_chatters, 0) as unique_chatters,
            COALESCE(c.top_emotes, '[]'::jsonb) as top_emotes,
            c.sentiment_score
        FROM latest_chat c
        FULL OUTER JOIN latest_viewer v
            ON c.timestamp = v.timestamp
    """

    try:
        pool = get_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(query, stream_id)
            return dict(row) if row else None
    except Exception as e:
        logger.error("Error fetching latest metrics", stream_id=stream_id, error=str(e))
        return None
