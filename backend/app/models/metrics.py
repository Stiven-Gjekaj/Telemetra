from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class ChatSummary(BaseModel):
    stream_id: str
    window_start: datetime
    window_end: datetime
    message_count: int
    unique_chatters: int
    emote_count: int
    avg_sentiment: float
    top_emotes: Optional[Dict[str, int]] = None
    top_chatters: Optional[Dict[str, int]] = None

class ViewerMetrics(BaseModel):
    stream_id: str
    timestamp: datetime
    viewer_count: int
    chatter_count: int
    subscriber_count: int

class Moment(BaseModel):
    stream_id: str
    moment_type: str
    timestamp: datetime
    description: Optional[str] = None
    severity: float
    metadata: Optional[Dict[str, Any]] = None
