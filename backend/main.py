from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import os
import redis.asyncio as aioredis
from datetime import datetime, timedelta
from typing import List, Optional

from database import get_pool, close_pool, execute_query, execute_one
from models import (
    StreamInfo,
    StreamListResponse,
    StreamMetricsResponse,
    ChatMetric,
    ViewerMetric,
    HealthResponse,
    StreamMetrics
)


# Redis client
redis_client: Optional[aioredis.Redis] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for startup and shutdown."""
    global redis_client

    # Startup: Initialize connections
    await get_pool()
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    redis_client = await aioredis.from_url(redis_url, decode_responses=True)

    yield

    # Shutdown: Close connections
    await close_pool()
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="Telemetra API",
    description="Real-time Twitch Analytics Platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, stream_id: str):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if stream_id not in self.active_connections:
            self.active_connections[stream_id] = []
        self.active_connections[stream_id].append(websocket)

    def disconnect(self, websocket: WebSocket, stream_id: str):
        """Remove a WebSocket connection."""
        if stream_id in self.active_connections:
            self.active_connections[stream_id].remove(websocket)
            if not self.active_connections[stream_id]:
                del self.active_connections[stream_id]

    async def broadcast(self, stream_id: str, message: dict):
        """Send a message to all connections for a stream."""
        if stream_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[stream_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, stream_id)


manager = ConnectionManager()


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Docker."""
    db_status = "healthy"
    redis_status = "healthy"

    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    try:
        if redis_client:
            await redis_client.ping()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

    return HealthResponse(
        status=status,
        database=db_status,
        redis=redis_status
    )


# Get list of streams
@app.get("/streams", response_model=StreamListResponse)
async def get_streams(status: Optional[str] = Query(None, description="Filter by status (live/offline)")):
    """Get list of available streams."""
    try:
        # Query distinct streams from chat_metrics table
        query = """
            SELECT DISTINCT ON (stream_id)
                stream_id,
                stream_id as channel_name,
                'live' as status,
                MIN(window_start) as started_at
            FROM chat_metrics
            GROUP BY stream_id
            ORDER BY stream_id, started_at DESC
        """

        rows = await execute_query(query)

        streams = [
            StreamInfo(
                stream_id=row['stream_id'],
                channel_name=row['channel_name'],
                status=row['status'],
                started_at=row['started_at']
            )
            for row in rows
        ]

        # Filter by status if provided
        if status:
            streams = [s for s in streams if s.status == status]

        return StreamListResponse(streams=streams)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# Get metrics for a specific stream
@app.get("/streams/{stream_id}/metrics", response_model=StreamMetricsResponse)
async def get_stream_metrics(
    stream_id: str,
    minutes: int = Query(30, ge=1, le=1440, description="Time window in minutes")
):
    """Get historical metrics for a stream."""
    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)

        # Query chat metrics
        chat_query = """
            SELECT window_start, message_count, unique_chatters
            FROM chat_metrics
            WHERE stream_id = $1
              AND window_start >= $2
              AND window_start <= $3
            ORDER BY window_start DESC
            LIMIT 100
        """
        chat_rows = await execute_query(chat_query, stream_id, start_time, end_time)

        # Query viewer metrics
        viewer_query = """
            SELECT timestamp, viewer_count
            FROM viewer_metrics
            WHERE stream_id = $1
              AND timestamp >= $2
              AND timestamp <= $3
            ORDER BY timestamp DESC
            LIMIT 100
        """
        viewer_rows = await execute_query(viewer_query, stream_id, start_time, end_time)

        # Convert to Pydantic models
        chat_metrics = [
            ChatMetric(
                window_start=row['window_start'],
                message_count=row['message_count'],
                unique_chatters=row['unique_chatters']
            )
            for row in chat_rows
        ]

        viewer_metrics = [
            ViewerMetric(
                timestamp=row['timestamp'],
                viewer_count=row['viewer_count']
            )
            for row in viewer_rows
        ]

        return StreamMetricsResponse(
            stream_id=stream_id,
            chat_metrics=chat_metrics,
            viewer_metrics=viewer_metrics
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# WebSocket endpoint for real-time updates
@app.websocket("/live/{stream_id}")
async def websocket_endpoint(websocket: WebSocket, stream_id: str):
    """WebSocket endpoint for real-time metric updates."""
    await manager.connect(websocket, stream_id)

    try:
        # Send initial data immediately
        try:
            # Get latest metrics from database
            chat_row = await execute_one(
                """
                SELECT window_start, message_count, unique_chatters
                FROM chat_metrics
                WHERE stream_id = $1
                ORDER BY window_start DESC
                LIMIT 1
                """,
                stream_id
            )

            viewer_row = await execute_one(
                """
                SELECT timestamp, viewer_count
                FROM viewer_metrics
                WHERE stream_id = $1
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                stream_id
            )

            if chat_row or viewer_row:
                initial_data = {
                    "stream_id": stream_id,
                    "timestamp": datetime.utcnow().isoformat()
                }

                if chat_row:
                    initial_data["chat"] = {
                        "window_start": chat_row['window_start'].isoformat(),
                        "message_count": chat_row['message_count'],
                        "unique_chatters": chat_row['unique_chatters']
                    }

                if viewer_row:
                    initial_data["viewers"] = {
                        "timestamp": viewer_row['timestamp'].isoformat(),
                        "viewer_count": viewer_row['viewer_count']
                    }

                await websocket.send_json(initial_data)

        except Exception as e:
            print(f"Error sending initial data: {e}")

        # Keep connection alive and send updates periodically
        while True:
            try:
                # Poll for new data every 5 seconds
                await asyncio.sleep(5)

                # Fetch latest metrics
                chat_row = await execute_one(
                    """
                    SELECT window_start, message_count, unique_chatters
                    FROM chat_metrics
                    WHERE stream_id = $1
                    ORDER BY window_start DESC
                    LIMIT 1
                    """,
                    stream_id
                )

                viewer_row = await execute_one(
                    """
                    SELECT timestamp, viewer_count
                    FROM viewer_metrics
                    WHERE stream_id = $1
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    stream_id
                )

                if chat_row or viewer_row:
                    update_data = {
                        "stream_id": stream_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }

                    if chat_row:
                        update_data["chat"] = {
                            "window_start": chat_row['window_start'].isoformat(),
                            "message_count": chat_row['message_count'],
                            "unique_chatters": chat_row['unique_chatters']
                        }

                    if viewer_row:
                        update_data["viewers"] = {
                            "timestamp": viewer_row['timestamp'].isoformat(),
                            "viewer_count": viewer_row['viewer_count']
                        }

                    await websocket.send_json(update_data)

            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error in WebSocket loop: {e}")
                await asyncio.sleep(5)

    except WebSocketDisconnect:
        manager.disconnect(websocket, stream_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, stream_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
