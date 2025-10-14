from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChatMetric(BaseModel):
    """Chat activity metric for a time window."""
    window_start: datetime
    message_count: int
    unique_chatters: int


class ViewerMetric(BaseModel):
    """Viewer count metric."""
    timestamp: datetime
    viewer_count: int


class StreamInfo(BaseModel):
    """Basic stream information."""
    stream_id: str
    channel_name: str
    status: str = "live"
    started_at: Optional[datetime] = None


class StreamMetrics(BaseModel):
    """Complete metrics for a stream."""
    stream_id: str
    chat: Optional[ChatMetric] = None
    viewers: Optional[ViewerMetric] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StreamMetricsResponse(BaseModel):
    """Response containing historical metrics."""
    stream_id: str
    chat_metrics: List[ChatMetric] = []
    viewer_metrics: List[ViewerMetric] = []


class StreamListResponse(BaseModel):
    """Response containing list of streams."""
    streams: List[StreamInfo]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str
    redis: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
