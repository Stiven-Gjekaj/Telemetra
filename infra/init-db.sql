-- ===========================
-- Telemetra Database Initialization
-- ===========================
-- Initial schema setup for development environment

-- Create streams table (metadata about streams)
CREATE TABLE IF NOT EXISTS streams (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create chat summary table (aggregated chat metrics per minute)
CREATE TABLE IF NOT EXISTS chat_summary_minute (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    chat_count INTEGER DEFAULT 0,
    unique_chatters INTEGER DEFAULT 0,
    top_emotes TEXT[], -- JSON array stored as text
    sentiment_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stream FOREIGN KEY (stream_id) REFERENCES streams(stream_id) ON DELETE CASCADE
);

-- Create viewer timeseries table (viewer count snapshots)
CREATE TABLE IF NOT EXISTS viewer_timeseries (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    viewer_count INTEGER NOT NULL,
    unique_viewers INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stream_viewers FOREIGN KEY (stream_id) REFERENCES streams(stream_id) ON DELETE CASCADE
);

-- Create transactions table (purchases and financial events)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    amount DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    transaction_type VARCHAR(50), -- 'subscription', 'tip', 'purchase'
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stream_transactions FOREIGN KEY (stream_id) REFERENCES streams(stream_id) ON DELETE CASCADE
);

-- Create moments table (detected anomalies and interesting events)
CREATE TABLE IF NOT EXISTS moments (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    moment_type VARCHAR(100) NOT NULL, -- 'chat_spike', 'viewer_surge', 'donation_surge', etc.
    detection_method VARCHAR(100), -- 'z_score', 'heuristic', 'ml_model'
    timestamp TIMESTAMP NOT NULL,
    value FLOAT,
    threshold FLOAT,
    context JSONB, -- Additional context about the moment
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_stream_moments FOREIGN KEY (stream_id) REFERENCES streams(stream_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_chat_summary_stream_window ON chat_summary_minute(stream_id, window_start DESC);
CREATE INDEX IF NOT EXISTS idx_viewer_timeseries_stream_ts ON viewer_timeseries(stream_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_stream_ts ON transactions(stream_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_moments_stream_ts ON moments(stream_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_moments_type ON moments(moment_type, timestamp DESC);

-- Create materialized view for top chatters (5 minute window)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_chatters_5m AS
SELECT
    stream_id,
    CURRENT_TIMESTAMP as computed_at,
    top_emotes as top_chatters
FROM chat_summary_minute
WHERE window_start > CURRENT_TIMESTAMP - INTERVAL '5 minutes'
ORDER BY window_start DESC
LIMIT 1;

-- Create materialized view for recent moments
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_anomalies AS
SELECT
    stream_id,
    moment_type,
    timestamp,
    value,
    threshold,
    context
FROM moments
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
ORDER BY timestamp DESC;

-- Grant permissions for application user (if different from postgres)
-- This is optional if using the same user
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO telemetra_app;

-- Insert demo stream for initial testing
INSERT INTO streams (stream_id, name, description)
VALUES ('demo_stream', 'Demo Stream', 'Demo stream for testing Telemetra MVP')
ON CONFLICT (stream_id) DO NOTHING;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for streams table
DROP TRIGGER IF EXISTS update_streams_updated_at ON streams;
CREATE TRIGGER update_streams_updated_at
    BEFORE UPDATE ON streams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
