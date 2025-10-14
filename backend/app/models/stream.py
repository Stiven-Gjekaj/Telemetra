from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class StreamBase(BaseModel):
    stream_id: str = Field(..., description="Unique stream identifier")
    channel_name: str = Field(..., description="Twitch channel name")
    title: Optional[str] = Field(None, description="Stream title")

class StreamCreate(StreamBase):
    pass

class StreamResponse(StreamBase):
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    is_live: bool
    total_viewers: int = 0
    peak_viewers: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
