-- Telemetra PostgreSQL Schema Initialization
-- Creates tables for streaming analytics data

-- Database setup
CREATE DATABASE IF NOT EXISTS telemetra;

-- Chat metrics table (aggregated by Spark from Kafka chat messages)
CREATE TABLE IF NOT EXISTS chat_metrics (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    message_count INTEGER NOT NULL,
    unique_chatters INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Unique constraint to prevent duplicate window aggregations
    UNIQUE(stream_id, window_start)
);

-- Viewer metrics table (raw viewer count snapshots)
CREATE TABLE IF NOT EXISTS viewer_metrics (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    viewer_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient time-series queries
CREATE INDEX idx_chat_metrics_stream_time ON chat_metrics(stream_id, window_start DESC);
CREATE INDEX idx_chat_metrics_window ON chat_metrics(window_start DESC);

CREATE INDEX idx_viewer_metrics_stream_time ON viewer_metrics(stream_id, timestamp DESC);
CREATE INDEX idx_viewer_metrics_timestamp ON viewer_metrics(timestamp DESC);

-- Optional: Create materialized view for recent chat activity (last 24 hours)
CREATE MATERIALIZED VIEW recent_chat_activity AS
SELECT
    stream_id,
    DATE_TRUNC('hour', window_start) as hour,
    SUM(message_count) as total_messages,
    AVG(unique_chatters) as avg_chatters
FROM chat_metrics
WHERE window_start >= NOW() - INTERVAL '24 hours'
GROUP BY stream_id, DATE_TRUNC('hour', window_start)
ORDER BY hour DESC;

-- Index on materialized view
CREATE INDEX idx_recent_chat_stream_hour ON recent_chat_activity(stream_id, hour DESC);

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO telemetra_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO telemetra_user;
GRANT SELECT ON recent_chat_activity TO telemetra_user;
