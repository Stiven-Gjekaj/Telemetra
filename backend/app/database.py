import databases
import sqlalchemy
from sqlalchemy import MetaData, Table, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://telemetra_user:telemetra_pass@localhost:5432/telemetra")

database = databases.Database(DATABASE_URL)
metadata = MetaData()

# Streams table
streams = Table(
    "streams",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("stream_id", String(100), unique=True, nullable=False, index=True),
    Column("channel_name", String(100), nullable=False, index=True),
    Column("title", String(500)),
    Column("started_at", DateTime, nullable=False, default=datetime.utcnow),
    Column("ended_at", DateTime),
    Column("is_live", Boolean, default=True),
    Column("total_viewers", Integer, default=0),
    Column("peak_viewers", Integer, default=0),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Chat summary per minute
chat_summary_minute = Table(
    "chat_summary_minute",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("stream_id", String(100), nullable=False, index=True),
    Column("window_start", DateTime, nullable=False, index=True),
    Column("window_end", DateTime, nullable=False),
    Column("message_count", Integer, default=0),
    Column("unique_chatters", Integer, default=0),
    Column("emote_count", Integer, default=0),
    Column("avg_sentiment", Float, default=0.0),
    Column("top_emotes", JSON),
    Column("top_chatters", JSON),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Viewer timeseries
viewer_timeseries = Table(
    "viewer_timeseries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("stream_id", String(100), nullable=False, index=True),
    Column("timestamp", DateTime, nullable=False, index=True),
    Column("viewer_count", Integer, default=0),
    Column("chatter_count", Integer, default=0),
    Column("subscriber_count", Integer, default=0),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Transactions (subscriptions, donations, etc.)
transactions = Table(
    "transactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("stream_id", String(100), nullable=False, index=True),
    Column("transaction_id", String(100), unique=True, nullable=False),
    Column("transaction_type", String(50), nullable=False),
    Column("username", String(100)),
    Column("amount", Float),
    Column("currency", String(10)),
    Column("message", Text),
    Column("timestamp", DateTime, nullable=False, index=True),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Moments (anomalies, highlights)
moments = Table(
    "moments",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("stream_id", String(100), nullable=False, index=True),
    Column("moment_type", String(50), nullable=False),
    Column("timestamp", DateTime, nullable=False, index=True),
    Column("description", Text),
    Column("severity", Float),
    Column("metadata", JSON),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Create engine
engine = sqlalchemy.create_engine(
    DATABASE_URL.replace("+asyncpg", ""),
    echo=False
)

async def init_db():
    """Initialize database tables"""
    metadata.create_all(engine)
