from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncpg
import redis.asyncio as redis
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global connections
db_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

# Active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup database connections"""
    global db_pool, redis_client

    # Startup
    database_url = os.getenv("DATABASE_URL")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

    logger.info("Connecting to database...")
    db_pool = await asyncpg.create_pool(
        database_url,
        min_size=5,
        max_size=20,
        command_timeout=60
    )

    logger.info("Connecting to Redis...")
    redis_client = await redis.from_url(redis_url, decode_responses=True)

    # Run migrations
    await run_migrations()

    logger.info("Application startup complete")

    yield

    # Shutdown
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Telemetra API",
    description="Real-time Twitch Analytics API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def run_migrations():
    """Run database migrations on startup"""
    async with db_pool.acquire() as conn:
        # Create streams table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS streams (
                id SERIAL PRIMARY KEY,
                stream_id VARCHAR(255) UNIQUE NOT NULL,
                channel_name VARCHAR(255) NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP,
                status VARCHAR(50) DEFAULT 'live',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create chat_summary_minute table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_summary_minute (
                id SERIAL PRIMARY KEY,
                stream_id VARCHAR(255) NOT NULL,
                window_start TIMESTAMP NOT NULL,
                window_end TIMESTAMP NOT NULL,
                message_count INTEGER NOT NULL,
                unique_chatters INTEGER NOT NULL,
                avg_message_length FLOAT,
                created_at TIMESTAMP DEFAULT NOW(),
                UNIQUE(stream_id, window_start)
            )
        """)

        # Create viewer_timeseries table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS viewer_timeseries (
                id SERIAL PRIMARY KEY,
                stream_id VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                viewer_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create transactions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                stream_id VARCHAR(255) NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                amount FLOAT NOT NULL,
                username VARCHAR(255),
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create moments table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS moments (
                id SERIAL PRIMARY KEY,
                stream_id VARCHAR(255) NOT NULL,
                moment_type VARCHAR(50) NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                metric_name VARCHAR(100),
                metric_value FLOAT,
                z_score FLOAT,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_stream_window ON chat_summary_minute(stream_id, window_start)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_viewer_stream_time ON viewer_timeseries(stream_id, timestamp)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_moments_stream_time ON moments(stream_id, timestamp)")

        logger.info("Database migrations completed")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        await redis_client.ping()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "up",
                "redis": "up"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.get("/streams")
async def get_streams(status: Optional[str] = "live", limit: int = 10):
    """Get list of streams"""
    try:
        async with db_pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    "SELECT * FROM streams WHERE status = $1 ORDER BY started_at DESC LIMIT $2",
                    status, limit
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM streams ORDER BY started_at DESC LIMIT $1",
                    limit
                )

            return {
                "streams": [dict(row) for row in rows],
                "count": len(rows)
            }
    except Exception as e:
        logger.error(f"Error fetching streams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/streams/{stream_id}/metrics")
async def get_stream_metrics(stream_id: str, minutes: int = 30):
    """Get metrics for a specific stream"""
    try:
        # Try Redis cache first
        cache_key = f"metrics:{stream_id}:{minutes}"
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        async with db_pool.acquire() as conn:
            # Get chat metrics
            chat_metrics = await conn.fetch("""
                SELECT window_start, message_count, unique_chatters, avg_message_length
                FROM chat_summary_minute
                WHERE stream_id = $1
                AND window_start >= NOW() - INTERVAL '%s minutes'
                ORDER BY window_start DESC
            """ % minutes, stream_id)

            # Get viewer metrics
            viewer_metrics = await conn.fetch("""
                SELECT timestamp, viewer_count
                FROM viewer_timeseries
                WHERE stream_id = $1
                AND timestamp >= NOW() - INTERVAL '%s minutes'
                ORDER BY timestamp DESC
            """ % minutes, stream_id)

            # Get recent transactions
            transactions = await conn.fetch("""
                SELECT transaction_type, amount, username, timestamp
                FROM transactions
                WHERE stream_id = $1
                AND timestamp >= NOW() - INTERVAL '%s minutes'
                ORDER BY timestamp DESC
            """ % minutes, stream_id)

            result = {
                "stream_id": stream_id,
                "chat_metrics": [dict(row) for row in chat_metrics],
                "viewer_metrics": [dict(row) for row in viewer_metrics],
                "transactions": [dict(row) for row in transactions],
                "timestamp": datetime.utcnow().isoformat()
            }

            # Cache for 10 seconds
            await redis_client.setex(cache_key, 10, json.dumps(result, default=str))

            return result
    except Exception as e:
        logger.error(f"Error fetching metrics for {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/streams/{stream_id}/moments")
async def get_stream_moments(stream_id: str, limit: int = 20):
    """Get detected moments/anomalies for a stream"""
    try:
        async with db_pool.acquire() as conn:
            moments = await conn.fetch("""
                SELECT moment_type, timestamp, metric_name, metric_value, z_score, description
                FROM moments
                WHERE stream_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """, stream_id, limit)

            return {
                "stream_id": stream_id,
                "moments": [dict(row) for row in moments],
                "count": len(moments)
            }
    except Exception as e:
        logger.error(f"Error fetching moments for {stream_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/live/{stream_id}")
async def websocket_endpoint(websocket: WebSocket, stream_id: str):
    """WebSocket endpoint for real-time stream updates"""
    await websocket.accept()

    # Add connection to active connections
    if stream_id not in active_connections:
        active_connections[stream_id] = []
    active_connections[stream_id].append(websocket)

    logger.info(f"WebSocket connected for stream {stream_id}")

    try:
        # Send initial data
        async with db_pool.acquire() as conn:
            latest_chat = await conn.fetchrow("""
                SELECT * FROM chat_summary_minute
                WHERE stream_id = $1
                ORDER BY window_start DESC
                LIMIT 1
            """, stream_id)

            latest_viewers = await conn.fetchrow("""
                SELECT * FROM viewer_timeseries
                WHERE stream_id = $1
                ORDER BY timestamp DESC
                LIMIT 1
            """, stream_id)

            await websocket.send_json({
                "type": "initial",
                "stream_id": stream_id,
                "chat": dict(latest_chat) if latest_chat else None,
                "viewers": dict(latest_viewers) if latest_viewers else None,
                "timestamp": datetime.utcnow().isoformat()
            })

        # Keep connection alive and send periodic updates
        import asyncio
        while True:
            # Wait for incoming messages or timeout
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                # Handle ping/pong or client messages if needed
            except asyncio.TimeoutError:
                # Send periodic update
                async with db_pool.acquire() as conn:
                    latest_chat = await conn.fetchrow("""
                        SELECT * FROM chat_summary_minute
                        WHERE stream_id = $1
                        ORDER BY window_start DESC
                        LIMIT 1
                    """, stream_id)

                    latest_viewers = await conn.fetchrow("""
                        SELECT * FROM viewer_timeseries
                        WHERE stream_id = $1
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """, stream_id)

                    await websocket.send_json({
                        "type": "update",
                        "stream_id": stream_id,
                        "chat": dict(latest_chat) if latest_chat else None,
                        "viewers": dict(latest_viewers) if latest_viewers else None,
                        "timestamp": datetime.utcnow().isoformat()
                    })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for stream {stream_id}")
        active_connections[stream_id].remove(websocket)
        if not active_connections[stream_id]:
            del active_connections[stream_id]
    except Exception as e:
        logger.error(f"WebSocket error for stream {stream_id}: {e}")
        if websocket in active_connections.get(stream_id, []):
            active_connections[stream_id].remove(websocket)


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    active_ws_count = sum(len(conns) for conns in active_connections.values())

    return {
        "active_websocket_connections": active_ws_count,
        "active_streams": len(active_connections),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
