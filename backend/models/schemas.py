"""
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: Optional[str] = Field(None, description="Database connectivity status")
    redis: Optional[str] = Field(None, description="Redis connectivity status")


class Stream(BaseModel):
    """Stream information."""
    stream_id: str = Field(..., description="Unique stream identifier")
    streamer_name: str = Field(..., description="Name of the streamer")
    title: Optional[str] = Field(None, description="Stream title")
    game_category: Optional[str] = Field(None, description="Game/category being streamed")
    started_at: datetime = Field(..., description="Stream start timestamp")
    is_live: bool = Field(default=True, description="Whether stream is currently live")
    viewer_count: Optional[int] = Field(None, description="Current viewer count")


class StreamMetrics(BaseModel):
    """Aggregated metrics for a stream."""
    stream_id: str = Field(..., description="Stream identifier")
    timestamp: datetime = Field(..., description="Metric timestamp")
    viewer_count: int = Field(..., description="Number of viewers")
    chat_rate: float = Field(..., description="Messages per minute")
    unique_chatters: int = Field(..., description="Unique chatters in window")
    top_emotes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top emotes with counts"
    )
    sentiment_score: Optional[float] = Field(
        None,
        description="Average sentiment score (-1 to 1)"
    )


class Moment(BaseModel):
    """Detected moment/anomaly in stream."""
    moment_id: Optional[int] = Field(None, description="Unique moment identifier")
    stream_id: str = Field(..., description="Stream identifier")
    timestamp: datetime = Field(..., description="When moment was detected")
    moment_type: str = Field(..., description="Type of moment (spike, drop, anomaly)")
    description: str = Field(..., description="Human-readable description")
    metric_name: str = Field(..., description="Metric that triggered detection")
    metric_value: float = Field(..., description="Value of the metric")
    threshold: Optional[float] = Field(None, description="Threshold that was exceeded")
    z_score: Optional[float] = Field(None, description="Z-score if anomaly detection")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class LiveMetricUpdate(BaseModel):
    """Real-time metric update pushed via WebSocket."""
    stream_id: str = Field(..., description="Stream identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    viewer_count: int = Field(..., description="Current viewer count")
    chat_rate: float = Field(..., description="Messages per minute")
    unique_chatters: Optional[int] = Field(None, description="Unique chatters")
    top_emotes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Top emotes"
    )
    sentiment_score: Optional[float] = Field(None, description="Sentiment score")
    recent_moments: List[Moment] = Field(
        default_factory=list,
        description="Recently detected moments"
    )


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
