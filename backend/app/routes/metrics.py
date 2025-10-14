from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from ..database import database, chat_summary_minute, viewer_timeseries, moments as moments_table
from ..models.metrics import ChatSummary, ViewerMetrics, Moment

router = APIRouter()

@router.get("/{stream_id}/metrics")
async def get_stream_metrics(
    stream_id: str,
    time_range: Optional[str] = "1h"
):
    """Get aggregated metrics for a stream"""
    # Parse time range
    time_ranges = {
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "24h": timedelta(hours=24)
    }

    delta = time_ranges.get(time_range, timedelta(hours=1))
    cutoff_time = datetime.utcnow() - delta

    # Get chat metrics
    chat_query = chat_summary_minute.select().where(
        (chat_summary_minute.c.stream_id == stream_id) &
        (chat_summary_minute.c.window_start >= cutoff_time)
    ).order_by(chat_summary_minute.c.window_start.desc())

    chat_results = await database.fetch_all(chat_query)

    # Get viewer metrics
    viewer_query = viewer_timeseries.select().where(
        (viewer_timeseries.c.stream_id == stream_id) &
        (viewer_timeseries.c.timestamp >= cutoff_time)
    ).order_by(viewer_timeseries.c.timestamp.desc())

    viewer_results = await database.fetch_all(viewer_query)

    return {
        "stream_id": stream_id,
        "time_range": time_range,
        "chat_metrics": [dict(row) for row in chat_results],
        "viewer_metrics": [dict(row) for row in viewer_results]
    }

@router.get("/{stream_id}/moments", response_model=List[dict])
async def get_stream_moments(
    stream_id: str,
    limit: int = 50
):
    """Get detected moments (anomalies, highlights) for a stream"""
    query = moments_table.select().where(
        moments_table.c.stream_id == stream_id
    ).order_by(moments_table.c.timestamp.desc()).limit(limit)

    results = await database.fetch_all(query)

    if not results:
        return []

    return [dict(row) for row in results]
