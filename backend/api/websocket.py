"""
WebSocket endpoint for real-time metric streaming.
"""
import asyncio
import json
from datetime import datetime
from typing import Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

from backend.config import settings
from backend.db.database import get_latest_metrics, get_stream_moments
from backend.db.redis_client import get_cached_metrics
from backend.models.schemas import LiveMetricUpdate, Moment

logger = structlog.get_logger(__name__)

# Create WebSocket router
ws_router = APIRouter()

# Track active connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    """Manages WebSocket connections for a stream."""

    def __init__(self):
        self.active_connections: dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, stream_id: str):
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            stream_id: Stream identifier
        """
        await websocket.accept()

        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = set()

        self.active_connections[stream_id].add(websocket)

        logger.info(
            "WebSocket connected",
            stream_id=stream_id,
            total_connections=len(self.active_connections[stream_id]),
        )

    def disconnect(self, websocket: WebSocket, stream_id: str):
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            stream_id: Stream identifier
        """
        if stream_id in self.active_connections:
            self.active_connections[stream_id].discard(websocket)

            if not self.active_connections[stream_id]:
                del self.active_connections[stream_id]

        logger.info(
            "WebSocket disconnected",
            stream_id=stream_id,
            remaining_connections=len(self.active_connections.get(stream_id, [])),
        )

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send a message to a specific connection.

        Args:
            message: Message data
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error("Error sending message", error=str(e))

    async def broadcast(self, message: dict, stream_id: str):
        """
        Broadcast a message to all connections for a stream.

        Args:
            message: Message data
            stream_id: Stream identifier
        """
        if stream_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[stream_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("Error broadcasting message", error=str(e))
                disconnected.add(connection)

        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection, stream_id)


# Global connection manager
manager = ConnectionManager()


async def get_metrics_update(stream_id: str) -> dict:
    """
    Get latest metrics for a stream from cache or database.

    Args:
        stream_id: Stream identifier

    Returns:
        Dictionary with metric data
    """
    # Try Redis cache first
    cached = await get_cached_metrics(stream_id)
    if cached:
        logger.debug("Using cached metrics", stream_id=stream_id)
        return cached

    # Fall back to database
    logger.debug("Fetching metrics from database", stream_id=stream_id)
    metrics = await get_latest_metrics(stream_id)

    if not metrics:
        # Return default values if no data
        return {
            "stream_id": stream_id,
            "timestamp": datetime.utcnow().isoformat(),
            "viewer_count": 0,
            "chat_rate": 0.0,
            "unique_chatters": 0,
            "top_emotes": [],
            "sentiment_score": None,
        }

    return {
        "stream_id": stream_id,
        "timestamp": metrics["timestamp"].isoformat() if hasattr(metrics["timestamp"], "isoformat") else str(metrics["timestamp"]),
        "viewer_count": metrics.get("viewer_count", 0),
        "chat_rate": metrics.get("chat_rate", 0.0),
        "unique_chatters": metrics.get("unique_chatters", 0),
        "top_emotes": metrics.get("top_emotes", []),
        "sentiment_score": metrics.get("sentiment_score"),
    }


async def get_recent_moments(stream_id: str, limit: int = 5) -> list[dict]:
    """
    Get recent moments for a stream.

    Args:
        stream_id: Stream identifier
        limit: Maximum number of moments

    Returns:
        List of moment dictionaries
    """
    try:
        moments = await get_stream_moments(stream_id=stream_id, limit=limit)
        return [
            {
                "moment_id": m.get("moment_id"),
                "stream_id": m["stream_id"],
                "timestamp": m["timestamp"].isoformat() if hasattr(m["timestamp"], "isoformat") else str(m["timestamp"]),
                "moment_type": m["moment_type"],
                "description": m["description"],
                "metric_name": m["metric_name"],
                "metric_value": m["metric_value"],
                "threshold": m.get("threshold"),
                "z_score": m.get("z_score"),
                "metadata": m.get("metadata", {}),
            }
            for m in moments
        ]
    except Exception as e:
        logger.error("Error fetching recent moments", stream_id=stream_id, error=str(e))
        return []


async def stream_metrics(websocket: WebSocket, stream_id: str):
    """
    Stream real-time metrics to a WebSocket client.

    Args:
        websocket: WebSocket connection
        stream_id: Stream identifier
    """
    try:
        while True:
            # Get latest metrics
            metrics = await get_metrics_update(stream_id)

            # Get recent moments
            moments = await get_recent_moments(stream_id, limit=5)

            # Construct update message
            update = {
                **metrics,
                "recent_moments": moments,
            }

            # Send to client
            await manager.send_personal_message(update, websocket)

            # Wait before next update
            await asyncio.sleep(settings.ws_message_interval)

    except WebSocketDisconnect:
        logger.info("Client disconnected", stream_id=stream_id)
        raise
    except Exception as e:
        logger.error("Error streaming metrics", stream_id=stream_id, error=str(e))
        raise


@ws_router.websocket("/live/{stream_id}")
async def websocket_endpoint(websocket: WebSocket, stream_id: str):
    """
    WebSocket endpoint for live metric streaming.

    Connects to a stream and pushes real-time metric updates every 1-2 seconds.
    Data is pulled from Redis cache or PostgreSQL database.

    Args:
        websocket: WebSocket connection
        stream_id: Stream identifier to subscribe to

    Example:
        Connect to ws://localhost:8000/live/demo_stream
        Receive JSON messages with real-time metrics
    """
    await manager.connect(websocket, stream_id)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connected",
                "stream_id": stream_id,
                "message": f"Connected to stream: {stream_id}",
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

        # Start streaming metrics
        await stream_metrics(websocket, stream_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, stream_id)
        logger.info("WebSocket disconnected normally", stream_id=stream_id)

    except Exception as e:
        manager.disconnect(websocket, stream_id)
        logger.error("WebSocket error", stream_id=stream_id, error=str(e))

        # Try to send error message before closing
        try:
            await websocket.send_json({
                "type": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
        except:
            pass


@ws_router.get("/live/health")
async def websocket_health():
    """
    Health check for WebSocket service.

    Returns:
        Dictionary with active connection statistics
    """
    total_connections = sum(len(conns) for conns in manager.active_connections.values())

    return {
        "status": "ok",
        "active_streams": len(manager.active_connections),
        "total_connections": total_connections,
        "streams": {
            stream_id: len(conns)
            for stream_id, conns in manager.active_connections.items()
        },
    }
