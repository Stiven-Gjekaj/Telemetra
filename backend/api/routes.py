"""
REST API endpoints for Telemetra.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List
import structlog

from backend.models.schemas import (
    HealthResponse,
    Stream,
    StreamMetrics,
    Moment,
    ErrorResponse,
)
from backend.db.database import (
    check_db_health,
    get_streams,
    get_stream_metrics,
    get_stream_moments,
)
from backend.db.redis_client import (
    check_redis_health,
    get_cached_streams_list,
    cache_streams_list,
    get_cached_metrics,
)

logger = structlog.get_logger(__name__)

# Create API router
router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service health status with database and Redis connectivity checks",
)
async def health_check():
    """
    Health check endpoint.

    Returns overall service health and checks connectivity to:
    - PostgreSQL database
    - Redis cache

    Returns:
        HealthResponse: Health status with component details
    """
    try:
        # Check database
        db_status = "ok" if await check_db_health() else "unavailable"

        # Check Redis
        redis_status = "ok" if await check_redis_health() else "unavailable"

        # Overall status is ok only if both are ok
        overall_status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

        logger.info(
            "Health check",
            status=overall_status,
            database=db_status,
            redis=redis_status,
        )

        return HealthResponse(
            status=overall_status,
            database=db_status,
            redis=redis_status,
        )

    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="error",
            database="error",
            redis="error",
        )


@router.get(
    "/streams",
    response_model=List[Stream],
    summary="List all streams",
    description="Get a list of all active streams with their current metrics",
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
)
async def list_streams(
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of streams to return"),
    offset: int = Query(default=0, ge=0, description="Number of streams to skip"),
):
    """
    Get list of all active streams.

    Args:
        limit: Maximum number of streams to return (1-500)
        offset: Number of streams to skip for pagination

    Returns:
        List[Stream]: List of active streams

    Raises:
        HTTPException: If database query fails
    """
    try:
        # Try to get from cache first
        if offset == 0:  # Only cache first page
            cached_streams = await get_cached_streams_list()
            if cached_streams:
                logger.debug("Returning cached streams list", count=len(cached_streams))
                return cached_streams[:limit]

        # Fetch from database
        logger.info("Fetching streams from database", limit=limit, offset=offset)
        streams = await get_streams(limit=limit, offset=offset)

        # Cache first page
        if offset == 0 and streams:
            await cache_streams_list(streams)

        logger.info("Streams fetched successfully", count=len(streams))
        return streams

    except Exception as e:
        logger.error("Error fetching streams", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch streams: {str(e)}"
        )


@router.get(
    "/streams/{stream_id}/metrics",
    response_model=List[StreamMetrics],
    summary="Get stream metrics",
    description="Get aggregated metrics for a specific stream",
    responses={
        404: {"model": ErrorResponse, "description": "Stream not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
)
async def get_metrics(
    stream_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of metric records"),
):
    """
    Get metrics for a specific stream.

    Args:
        stream_id: Unique stream identifier
        limit: Maximum number of metric records to return (1-1000)

    Returns:
        List[StreamMetrics]: List of metric records ordered by timestamp (newest first)

    Raises:
        HTTPException: If stream not found or database query fails
    """
    try:
        logger.info("Fetching metrics", stream_id=stream_id, limit=limit)

        # Fetch metrics from database
        metrics = await get_stream_metrics(stream_id=stream_id, limit=limit)

        if not metrics:
            logger.warning("No metrics found", stream_id=stream_id)
            raise HTTPException(
                status_code=404,
                detail=f"No metrics found for stream: {stream_id}"
            )

        # Convert to response model
        result = []
        for metric in metrics:
            result.append(StreamMetrics(
                stream_id=stream_id,
                timestamp=metric["timestamp"],
                viewer_count=metric["viewer_count"],
                chat_rate=metric["chat_rate"],
                unique_chatters=metric["unique_chatters"],
                top_emotes=metric["top_emotes"] if isinstance(metric["top_emotes"], list) else [],
                sentiment_score=metric.get("sentiment_score"),
            ))

        logger.info("Metrics fetched successfully", stream_id=stream_id, count=len(result))
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching metrics", stream_id=stream_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch metrics: {str(e)}"
        )


@router.get(
    "/streams/{stream_id}/moments",
    response_model=List[Moment],
    summary="Get stream moments",
    description="Get detected moments and anomalies for a specific stream",
    responses={
        404: {"model": ErrorResponse, "description": "Stream not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
)
async def get_moments(
    stream_id: str,
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of moments"),
):
    """
    Get detected moments/anomalies for a stream.

    Args:
        stream_id: Unique stream identifier
        limit: Maximum number of moments to return (1-200)

    Returns:
        List[Moment]: List of detected moments ordered by timestamp (newest first)

    Raises:
        HTTPException: If stream not found or database query fails
    """
    try:
        logger.info("Fetching moments", stream_id=stream_id, limit=limit)

        # Fetch moments from database
        moments = await get_stream_moments(stream_id=stream_id, limit=limit)

        if not moments:
            logger.info("No moments found", stream_id=stream_id)
            return []  # Return empty list instead of 404

        # Convert to response model
        result = []
        for moment in moments:
            result.append(Moment(
                moment_id=moment.get("moment_id"),
                stream_id=moment["stream_id"],
                timestamp=moment["timestamp"],
                moment_type=moment["moment_type"],
                description=moment["description"],
                metric_name=moment["metric_name"],
                metric_value=moment["metric_value"],
                threshold=moment.get("threshold"),
                z_score=moment.get("z_score"),
                metadata=moment.get("metadata", {}),
            ))

        logger.info("Moments fetched successfully", stream_id=stream_id, count=len(result))
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching moments", stream_id=stream_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch moments: {str(e)}"
        )
