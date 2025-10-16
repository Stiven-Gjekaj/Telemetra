# Integrating Spark Streaming into Telemetra

This guide explains how to integrate the Spark streaming job into your main Telemetra Docker Compose setup.

## Integration Steps

### 1. Main Docker Compose Integration

Add the following to your `infra/docker-compose.yml`:

```yaml
services:
  # ... existing services (kafka, postgres, etc.) ...

  # Spark Streaming Analytics
  spark-streaming:
    build:
      context: ../data_pipeline/spark
      dockerfile: Dockerfile
    container_name: telemetra-spark-streaming
    hostname: spark-streaming
    environment:
      # Kafka Configuration
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092

      # PostgreSQL Configuration
      POSTGRES_URL: jdbc:postgresql://postgres:5432/telemetra
      POSTGRES_USER: ${POSTGRES_USER:-telemetra}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-telemetra}

      # Spark Configuration
      SPARK_MASTER: local[*]
      SPARK_DRIVER_MEMORY: ${SPARK_DRIVER_MEMORY:-2g}
      SPARK_EXECUTOR_MEMORY: ${SPARK_EXECUTOR_MEMORY:-2g}
      SPARK_EXECUTOR_CORES: ${SPARK_EXECUTOR_CORES:-2}

      # Job Configuration
      CHECKPOINT_LOCATION: /tmp/spark-checkpoints
      ANOMALY_THRESHOLD: ${ANOMALY_THRESHOLD:-3.0}

      # Logging
      PYTHONUNBUFFERED: 1

    depends_on:
      kafka:
        condition: service_healthy
      postgres:
        condition: service_healthy

    volumes:
      - spark-checkpoints:/tmp/spark-checkpoints
      - spark-events:/tmp/spark-events

    ports:
      - "4040:4040"  # Spark UI

    networks:
      - telemetra-network

    restart: unless-stopped

    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

    healthcheck:
      test: ["CMD", "pgrep", "-f", "spark_streaming_job"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  # ... existing volumes ...
  spark-checkpoints:
  spark-events:
```

### 2. Environment Variables

Add to your `.env` file:

```bash
# Spark Configuration
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g
SPARK_EXECUTOR_CORES=2
ANOMALY_THRESHOLD=3.0
```

Add to your `.env.example`:

```bash
# Spark Streaming Configuration
SPARK_DRIVER_MEMORY=2g
SPARK_EXECUTOR_MEMORY=2g
SPARK_EXECUTOR_CORES=2
ANOMALY_THRESHOLD=3.0
```

### 3. Database Schema

Ensure your database migrations create the required tables. Add to `backend/migrations/`:

```sql
-- File: 003_create_analytics_tables.sql

-- Chat summary aggregations table (partitioned by date for performance)
CREATE TABLE IF NOT EXISTS chat_summary_minute (
    id SERIAL,
    stream_id VARCHAR(255) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    chat_count INTEGER DEFAULT 0,
    unique_chatters INTEGER DEFAULT 0,
    avg_sentiment DOUBLE PRECISION,
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    chat_rate DOUBLE PRECISION,
    avg_viewers DOUBLE PRECISION,
    top_emotes TEXT[],
    z_score DOUBLE PRECISION,
    is_anomaly BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, window_start)
) PARTITION BY RANGE (window_start);

-- Create partitions for current and next month
CREATE TABLE chat_summary_minute_2024_10 PARTITION OF chat_summary_minute
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE chat_summary_minute_2024_11 PARTITION OF chat_summary_minute
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

-- Indexes for query performance
CREATE INDEX idx_chat_summary_stream ON chat_summary_minute(stream_id, window_start DESC);
CREATE INDEX idx_chat_summary_anomaly ON chat_summary_minute(stream_id, window_start) WHERE is_anomaly = TRUE;

-- Moments/anomalies table
CREATE TABLE IF NOT EXISTS moments (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    moment_type VARCHAR(50) NOT NULL,
    description TEXT,
    intensity DOUBLE PRECISION,
    metadata JSONB,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for moments
CREATE INDEX idx_moments_stream ON moments(stream_id, timestamp DESC);
CREATE INDEX idx_moments_type ON moments(moment_type, timestamp DESC);
CREATE INDEX idx_moments_detected ON moments(detected_at DESC);
```

### 4. Startup Sequence

Update your startup script or `Makefile` to ensure proper service ordering:

```makefile
# File: Makefile

.PHONY: start

start:
	@echo "Starting Telemetra services..."
	# Start infrastructure first
	docker compose -f infra/docker-compose.yml up -d postgres kafka redis
	@echo "Waiting for infrastructure to be ready..."
	sleep 15
	# Run database migrations
	docker compose -f infra/docker-compose.yml run --rm backend alembic upgrade head
	# Start application services
	docker compose -f infra/docker-compose.yml up -d backend frontend
	# Start data pipeline
	docker compose -f infra/docker-compose.yml up -d mock-producer spark-streaming
	@echo "All services started! Dashboard: http://localhost:3000"
```

### 5. Verification Steps

After integration, verify the setup:

```bash
# 1. Check all services are running
docker compose -f infra/docker-compose.yml ps

# 2. Verify Spark is processing data
docker logs telemetra-spark-streaming --tail 50

# 3. Check Spark UI
curl -I http://localhost:4040

# 4. Query aggregated data
docker exec -it telemetra-postgres psql -U telemetra -d telemetra -c \
  "SELECT COUNT(*) FROM chat_summary_minute;"

# 5. Check for detected moments
docker exec -it telemetra-postgres psql -U telemetra -d telemetra -c \
  "SELECT * FROM moments ORDER BY detected_at DESC LIMIT 5;"
```

### 6. Monitoring Integration

#### Prometheus Metrics

Add to `infra/prometheus.yml`:

```yaml
scrape_configs:
  # ... existing configs ...

  - job_name: 'spark'
    static_configs:
      - targets: ['spark-streaming:4040']
    metrics_path: '/metrics/prometheus'
```

#### Grafana Dashboard

Import the Spark monitoring dashboard:

1. Open Grafana: `http://localhost:3001`
2. Go to Dashboards → Import
3. Upload: `data_pipeline/spark/grafana/spark-dashboard.json`

### 7. Development Workflow

For local development with hot-reload:

```yaml
# docker-compose.override.yml (for development)
services:
  spark-streaming:
    volumes:
      - ../data_pipeline/spark/spark_streaming_job.py:/app/spark_streaming_job.py
    environment:
      - DEV_MODE=true
      - LOG_LEVEL=DEBUG
```

Then restart when you modify the code:

```bash
docker compose restart spark-streaming
```

## Service Dependencies Graph

```
┌─────────────┐
│   Kafka     │◄──── telemetra.events.chat
│   (9092)    │◄──── telemetra.events.viewer
└──────┬──────┘
       │
       │ consumes
       ▼
┌──────────────────────┐
│  Spark Streaming     │
│  (spark_streaming    │
│   _job.py)           │
│                      │
│  • Windowing         │
│  • Sentiment         │
│  • Anomaly Detection │
└──────┬───────────────┘
       │
       │ writes (JDBC)
       ▼
┌─────────────────────┐
│   PostgreSQL        │
│   (5432)            │
│                     │
│  Tables:            │
│  • chat_summary_    │
│    minute           │
│  • moments          │
└─────────────────────┘
       ▲
       │ reads
       │
┌──────┴───────┐
│   Backend    │
│   (FastAPI)  │
│   (8000)     │
└──────────────┘
```

## Troubleshooting Integration Issues

### Issue: Spark can't connect to Kafka

**Symptoms:**
```
ERROR: Kafka not available after 60 attempts
```

**Solution:**
- Ensure Kafka container is healthy: `docker ps | grep kafka`
- Check network connectivity: `docker exec spark-streaming nc -zv kafka 9092`
- Verify Kafka is accepting connections: `docker logs telemetra-kafka`

### Issue: Database connection refused

**Symptoms:**
```
ERROR: PostgreSQL not available
```

**Solution:**
- Ensure PostgreSQL is running: `docker ps | grep postgres`
- Verify database exists:
  ```bash
  docker exec -it telemetra-postgres psql -U telemetra -l
  ```
- Check PostgreSQL logs: `docker logs telemetra-postgres`

### Issue: Tables don't exist

**Symptoms:**
```
org.postgresql.util.PSQLException: ERROR: relation "chat_summary_minute" does not exist
```

**Solution:**
- Run migrations:
  ```bash
  docker compose -f infra/docker-compose.yml run --rm backend alembic upgrade head
  ```
- Or manually create tables using SQL from step 3

### Issue: Checkpoint recovery failed

**Symptoms:**
```
ERROR: Unable to recover from checkpoint
```

**Solution:**
- For development, clean checkpoints:
  ```bash
  docker volume rm telemetra_spark-checkpoints
  docker compose -f infra/docker-compose.yml up -d spark-streaming
  ```
- For production, investigate checkpoint corruption and restore from backup

## Performance Optimization

### For High-Volume Streams

Adjust these environment variables:

```bash
# Increase processing capacity
SPARK_EXECUTOR_MEMORY=8g
SPARK_EXECUTOR_CORES=4

# Increase batch size
MAX_OFFSETS_PER_TRIGGER=50000

# Faster micro-batches
TRIGGER_INTERVAL=5 seconds
```

### For Low-Latency Requirements

```bash
# Smaller batches
MAX_OFFSETS_PER_TRIGGER=1000

# Near real-time processing
TRIGGER_INTERVAL=1 second

# Reduce watermark
WATERMARK_DELAY=5 seconds
```

### Resource Limits

Adjust Docker resource limits based on your environment:

```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Use more CPU
      memory: 8G        # Allocate more memory
    reservations:
      cpus: '2.0'
      memory: 4G
```

## Next Steps

After successful integration:

1. **Monitor Performance**: Check Spark UI regularly for bottlenecks
2. **Set Up Alerts**: Configure alerts for processing delays
3. **Tune Parameters**: Adjust window sizes and thresholds based on your data
4. **Test Failover**: Verify checkpoint recovery works correctly
5. **Scale Up**: Add more executors for higher throughput if needed

For production deployment, see [Production Deployment Guide](PRODUCTION.md).
