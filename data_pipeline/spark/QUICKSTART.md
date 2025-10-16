# Telemetra Spark Streaming - Quick Start Guide

Get the Spark streaming job running in under 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 4040, 9092, 5432 available

## Quick Start (3 Steps)

### Step 1: Start Infrastructure

Start Kafka and PostgreSQL:

```bash
# From project root
cd infra
docker compose up -d kafka postgres
```

Wait for services to be ready (about 30 seconds):

```bash
docker compose ps
```

### Step 2: Create Database Tables

Run migrations to create required tables:

```bash
docker exec -it telemetra-postgres psql -U telemetra -d telemetra << 'EOF'
CREATE TABLE IF NOT EXISTS chat_summary_minute (
    id SERIAL PRIMARY KEY,
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
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE INDEX idx_chat_summary_stream ON chat_summary_minute(stream_id, window_start DESC);
CREATE INDEX idx_moments_stream ON moments(stream_id, timestamp DESC);
EOF
```

### Step 3: Start Spark Streaming Job

```bash
# From data_pipeline/spark directory
cd ../data_pipeline/spark
docker compose -f docker-compose.spark.yml up -d
```

### Verify It's Running

```bash
# Check logs
docker logs telemetra-spark-streaming --tail 50

# You should see:
# ✓ Kafka is available
# ✓ PostgreSQL is available
# Starting Spark Streaming Job...
# Streaming queries started successfully
```

### View Spark UI

Open in browser: [http://localhost:4040](http://localhost:4040)

## Testing the Pipeline

### Generate Test Data

Start the mock producer to generate sample events:

```bash
# From project root
cd data_pipeline/producer
python twitch_mock_producer.py
```

Or with Docker:

```bash
docker compose -f infra/docker-compose.yml up -d mock-producer
```

### Verify Data Processing

Check that data is being aggregated:

```bash
# Query chat summaries (wait ~60 seconds for first window)
docker exec -it telemetra-postgres psql -U telemetra -d telemetra -c \
  "SELECT stream_id, window_start, chat_count, unique_chatters, chat_rate
   FROM chat_summary_minute
   ORDER BY window_start DESC
   LIMIT 5;"
```

Expected output:
```
 stream_id  |    window_start     | chat_count | unique_chatters | chat_rate
------------+---------------------+------------+-----------------+-----------
 demo_stream| 2024-10-16 10:15:00 |         42 |              15 |      0.70
 demo_stream| 2024-10-16 10:14:00 |         38 |              12 |      0.63
 ...
```

Check for anomalies/moments:

```bash
docker exec -it telemetra-postgres psql -U telemetra -d telemetra -c \
  "SELECT stream_id, timestamp, moment_type, description, intensity
   FROM moments
   ORDER BY detected_at DESC
   LIMIT 5;"
```

## Common Commands

### View Logs
```bash
docker logs -f telemetra-spark-streaming
```

### Restart Job
```bash
docker compose -f docker-compose.spark.yml restart spark-streaming
```

### Stop Job
```bash
docker compose -f docker-compose.spark.yml stop spark-streaming
```

### Clean Checkpoints (fresh start)
```bash
docker compose -f docker-compose.spark.yml down -v
docker compose -f docker-compose.spark.yml up -d
```

## Troubleshooting

### "Kafka not available"
```bash
# Check Kafka is running
docker ps | grep kafka

# Restart Kafka
docker compose -f infra/docker-compose.yml restart kafka

# Wait 30 seconds and restart Spark
docker compose -f docker-compose.spark.yml restart spark-streaming
```

### "No data appearing in database"
```bash
# 1. Verify producer is running
docker ps | grep producer

# 2. Check Kafka has messages
docker exec -it telemetra-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --from-beginning \
  --max-messages 5

# 3. Check Spark logs for errors
docker logs telemetra-spark-streaming | grep ERROR
```

### "Tables don't exist"
```bash
# Re-run Step 2 to create tables
# Or check if migrations need to run
docker compose -f infra/docker-compose.yml run --rm backend alembic upgrade head
```

### "Out of memory"
```bash
# Increase memory limits in docker-compose.spark.yml
# Or in environment:
export SPARK_DRIVER_MEMORY=4g
export SPARK_EXECUTOR_MEMORY=4g
docker compose -f docker-compose.spark.yml up -d
```

## Next Steps

### 1. Adjust Anomaly Sensitivity

Edit `.env`:
```bash
# Lower = more sensitive (more anomalies detected)
# Higher = less sensitive (fewer anomalies)
ANOMALY_THRESHOLD=2.5  # Default is 3.0
```

Restart:
```bash
docker compose -f docker-compose.spark.yml restart spark-streaming
```

### 2. Monitor Performance

Watch Spark UI Streaming tab:
- Processing time should be < 10 seconds
- Input rate shows messages/second
- Batch duration shows processing speed

### 3. Scale Up

For higher throughput, increase resources:

```yaml
# docker-compose.spark.yml
environment:
  SPARK_EXECUTOR_MEMORY: 4g
  SPARK_EXECUTOR_CORES: 4
deploy:
  resources:
    limits:
      cpus: '4.0'
      memory: 8G
```

### 4. Production Deployment

See [INTEGRATION.md](INTEGRATION.md) for full production setup including:
- Checkpoint backup/recovery
- Monitoring and alerting
- Cluster deployment
- Performance tuning

## Architecture Overview

```
┌─────────────────┐
│  Mock Producer  │─────┐
│  (Python)       │     │
└─────────────────┘     │
                        ▼
                 ┌──────────────┐
                 │    Kafka     │
                 │  Topics:     │
                 │  • chat      │
                 │  • viewer    │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────────┐
                 │ Spark Streaming  │
                 │  • Windowing     │
                 │  • Sentiment     │
                 │  • Anomalies     │
                 └──────┬───────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  PostgreSQL  │
                 │  Tables:     │
                 │  • summaries │
                 │  • moments   │
                 └──────────────┘
```

## Sample Queries

### Top Streams by Chat Activity
```sql
SELECT
    stream_id,
    AVG(chat_rate) as avg_chat_rate,
    MAX(chat_count) as peak_messages,
    SUM(unique_chatters) as total_unique_users
FROM chat_summary_minute
WHERE window_start > NOW() - INTERVAL '1 hour'
GROUP BY stream_id
ORDER BY avg_chat_rate DESC;
```

### Recent Anomalies
```sql
SELECT
    stream_id,
    window_start,
    chat_count,
    chat_rate,
    z_score,
    top_emotes
FROM chat_summary_minute
WHERE is_anomaly = true
    AND window_start > NOW() - INTERVAL '1 hour'
ORDER BY z_score DESC;
```

### Sentiment Trends
```sql
SELECT
    stream_id,
    DATE_TRUNC('hour', window_start) as hour,
    AVG(avg_sentiment) as sentiment,
    SUM(positive_count) as positive_msgs,
    SUM(negative_count) as negative_msgs
FROM chat_summary_minute
WHERE window_start > NOW() - INTERVAL '24 hours'
GROUP BY stream_id, hour
ORDER BY hour DESC;
```

## Resources

- [Full Documentation](README.md)
- [Integration Guide](INTEGRATION.md)
- [Apache Spark Docs](https://spark.apache.org/docs/latest/)
- [PySpark API Reference](https://spark.apache.org/docs/latest/api/python/)

## Support

For issues or questions:
1. Check logs: `docker logs telemetra-spark-streaming`
2. Review [Troubleshooting](#troubleshooting) section
3. See [INTEGRATION.md](INTEGRATION.md) for detailed setup
4. Check Spark UI at http://localhost:4040

Happy streaming! 🚀
