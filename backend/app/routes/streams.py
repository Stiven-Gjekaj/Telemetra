from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from ..database import database, streams as streams_table
from ..models.stream import Stream, StreamCreate, StreamResponse

router = APIRouter()

@router.get("/", response_model=List[StreamResponse])
async def list_streams(
    is_live: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
):
    """List all streams with optional filters"""
    query = streams_table.select()

    if is_live is not None:
        query = query.where(streams_table.c.is_live == is_live)

    query = query.order_by(streams_table.c.started_at.desc())
    query = query.limit(limit).offset(offset)

    results = await database.fetch_all(query)
    return [dict(row) for row in results]

@router.get("/{stream_id}", response_model=StreamResponse)
async def get_stream(stream_id: str):
    """Get details for a specific stream"""
    query = streams_table.select().where(streams_table.c.stream_id == stream_id)
    result = await database.fetch_one(query)

    if result is None:
        raise HTTPException(status_code=404, detail="Stream not found")

    return dict(result)

@router.post("/", response_model=StreamResponse)
async def create_stream(stream: StreamCreate):
    """Create a new stream"""
    query = streams_table.insert().values(
        stream_id=stream.stream_id,
        channel_name=stream.channel_name,
        title=stream.title,
        started_at=datetime.utcnow(),
        is_live=True
    )

    last_record_id = await database.execute(query)

    # Fetch the created stream
    query = streams_table.select().where(streams_table.c.id == last_record_id)
    result = await database.fetch_one(query)

    return dict(result)
