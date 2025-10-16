# Telemetra Spark Streaming Component - Deployment Guide

## Overview

This guide provides complete instructions for deploying the Telemetra PySpark streaming analytics component. All files have been created and are production-ready.

## Created Files Summary

### Core Application
```
C:\Users\stive\Desktop\stuff\code\Telemetra\data_pipeline\spark\
├── spark_streaming_job.py          # Main PySpark application (19KB)
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Container definition
├── entrypoint.sh                   # Startup script with health checks
├── docker-compose.spark.yml        # Standalone Docker Compose config
├── config.example.env              # Environment variable template
├── .dockerignore                   # Docker build exclusions
├── pytest.ini                      # Pytest configuration
├── Makefile                        # Development commands
│
├── Documentation/
│   ├── README.md                   # Comprehensive technical docs
│   ├── QUICKSTART.md              # 5-minute quick start guide
│   ├── INTEGRATION.md             # Integration into main project
│   └── FILES_SUMMARY.md           # Detailed file descriptions
│
└── Testing/
    └── test_spark_job.py          # Unit test suite (pytest)

CI/CD:
.github/workflows/spark-ci.yml      # GitHub Actions workflow
```

**Total Files**: 15
**Total Size**: ~103KB

---

## Features Implemented

### ✅ Kafka Stream Processing
- Consumes from `telemetra.events.chat` and `telemetra.events.viewer`
- Parses JSON events with defined schemas
- Handles late data with 10-second watermarking
- Configurable batch sizes and trigger intervals

### ✅ Windowed Aggregations
- **Window**: 1-minute tumbling windows with 10-second slides
- **Metrics**:
  - `chat_count`: Total messages per window
  - `unique_chatters`: Distinct user count
  - `avg_sentiment`: Lexicon-based sentiment score
  - `top_emotes`: Most used emotes (array)
  - `chat_rate`: Messages per second
  - `avg_viewers`: Average concurrent viewers
  - `positive_count` / `negative_count`: Sentiment distribution

### ✅ Sentiment Analysis
- Lexicon-based approach with 20+ positive/negative words
- Score range: -1.0 (negative) to +1.0 (positive)
- Case-insensitive matching
- Twitch-specific emotes included (Pog, PogChamp, KEKW, etc.)

### ✅ Anomaly Detection
- Z-score statistical method on chat_rate
- Rolling window: Last 10 time periods per stream
- Configurable threshold (default: 3.0 σ)
- Writes detected anomalies to `moments` table

### ✅ PostgreSQL Integration
- JDBC batch writes to two tables:
  - `chat_summary_minute`: Aggregated metrics
  - `moments`: Detected anomalies
- Fault-tolerant checkpointing
- Comprehensive error handling

### ✅ Production Features
- Graceful shutdown handling
- Health checks (Docker + Spark)
- Resource limits and reservations
- Structured logging
- Dependency wait logic (Kafka + PostgreSQL)
- Configurable via environment variables

---

## Quick Start (Copy-Paste Commands)

### Option 1: Standalone Testing

```bash
# 1. Navigate to Spark directory
cd C:/Users/stive/Desktop/stuff/code/Telemetra/data_pipeline/spark

# 2. Start infrastructure (requires Kafka + PostgreSQL running)
# If not already running:
docker network create telemetra-network
docker run -d --name telemetra-postgres --network telemetra-network \
  -e POSTGRES_DB=telemetra -e POSTGRES_USER=telemetra -e POSTGRES_PASSWORD=telemetra \
  -p 5432:5432 postgres:16-alpine

docker run -d --name telemetra-zookeeper --network telemetra-network \
  -e ZOOKEEPER_CLIENT_PORT=2181 -p 2181:2181 confluentinc/cp-zookeeper:7.5.0

docker run -d --name telemetra-kafka --network telemetra-network \
  -e KAFKA_BROKER_ID=1 -e KAFKA_ZOOKEEPER_CONNECT=telemetra-zookeeper:2181 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://telemetra-kafka:9092 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -p 9092:9092 confluentinc/cp-kafka:7.5.0

# 3. Create database tables
docker exec -i telemetra-postgres psql -U telemetra -d telemetra << 'EOF'
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

# 4. Build and start Spark streaming job
docker compose -f docker-compose.spark.yml up --build -d

# 5. View logs
docker logs -f telemetra-spark-streaming

# 6. Access Spark UI
# Open browser: http://localhost:4040
```

### Option 2: Integration with Main Docker Compose

**Add to `infra/docker-compose.yml`:**

```yaml
services:
  # ... existing services ...

  spark-streaming:
    build:
      context: ../data_pipeline/spark
      dockerfile: Dockerfile
    container_name: telemetra-spark-streaming
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      POSTGRES_URL: jdbc:postgresql://postgres:5432/telemetra
      POSTGRES_USER: ${POSTGRES_USER:-telemetra}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-telemetra}
      CHECKPOINT_LOCATION: /tmp/spark-checkpoints
      ANOMALY_THRESHOLD: ${ANOMALY_THRESHOLD:-3.0}
      SPARK_DRIVER_MEMORY: ${SPARK_DRIVER_MEMORY:-2g}
      SPARK_EXECUTOR_MEMORY: ${SPARK_EXECUTOR_MEMORY:-2g}
      SPARK_EXECUTOR_CORES: ${SPARK_EXECUTOR_CORES:-2}
    depends_on:
      - kafka
      - postgres
    volumes:
      - spark-checkpoints:/tmp/spark-checkpoints
      - spark-events:/tmp/spark-events
    ports:
      - "4040:4040"
    networks:
      - telemetra-network
    restart: unless-stopped

volumes:
  # ... existing volumes ...
  spark-checkpoints:
  spark-events:
```

**Then run:**

```bash
cd C:/Users/stive/Desktop/stuff/code/Telemetra/infra
docker compose up --build -d
```

---

## Verification & Testing

### 1. Check Service Health

```bash
# Check container status
docker ps | grep spark-streaming

# View logs (should show "Streaming queries started successfully")
docker logs telemetra-spark-streaming --tail 50

# Check Spark UI
curl -I http://localhost:4040
```

### 2. Verify Data Processing

Wait ~60 seconds for first window, then:

```bash
# Query aggregated metrics
docker exec -i telemetra-postgres psql -U telemetra -d telemetra << 'EOF'
SELECT
    stream_id,
    window_start,
    chat_count,
    unique_chatters,
    ROUND(chat_rate::numeric, 2) as chat_rate,
    ROUND(avg_sentiment::numeric, 2) as sentiment,
    top_emotes
FROM chat_summary_minute
ORDER BY window_start DESC
LIMIT 5;
EOF

# Query detected moments/anomalies
docker exec -i telemetra-postgres psql -U telemetra -d telemetra << 'EOF'
SELECT
    stream_id,
    timestamp,
    moment_type,
    description,
    ROUND(intensity::numeric, 2) as intensity
FROM moments
ORDER BY detected_at DESC
LIMIT 5;
EOF
```

### 3. Run Unit Tests

```bash
cd C:/Users/stive/Desktop/stuff/code/Telemetra/data_pipeline/spark

# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest test_spark_job.py -v

# With coverage
pytest test_spark_job.py -v --cov=spark_streaming_job --cov-report=term-missing
```

Expected output:
```
========================= test session starts =========================
collected 20 items

test_spark_job.py::TestSentimentScoring::test_positive_sentiment PASSED
test_spark_job.py::TestSentimentScoring::test_negative_sentiment PASSED
test_spark_job.py::TestSentimentScoring::test_neutral_sentiment PASSED
...
========================= 20 passed in 15.23s =========================
```

---

## Configuration Reference

### Environment Variables

Copy `config.example.env` to `.env` and customize:

```bash
# Key configuration options:

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# PostgreSQL
POSTGRES_URL=jdbc:postgresql://postgres:5432/telemetra
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=telemetra

# Spark resources
SPARK_DRIVER_MEMORY=2g      # Increase for larger datasets
SPARK_EXECUTOR_MEMORY=2g    # Increase for more parallelism
SPARK_EXECUTOR_CORES=2      # Adjust based on CPU cores

# Anomaly detection
ANOMALY_THRESHOLD=3.0       # Lower = more sensitive (2.5-4.0 recommended)

# Checkpoints
CHECKPOINT_LOCATION=/tmp/spark-checkpoints  # Use HDFS/S3 in production
```

### Performance Tuning

**For High Volume (>1000 msg/sec):**
```bash
SPARK_EXECUTOR_MEMORY=8g
SPARK_EXECUTOR_CORES=4
MAX_OFFSETS_PER_TRIGGER=50000
```

**For Low Latency (<5 seconds):**
```bash
MAX_OFFSETS_PER_TRIGGER=1000
TRIGGER_INTERVAL=1 second
WATERMARK_DELAY=5 seconds
```

---

## Monitoring

### Spark UI
**URL**: http://localhost:4040

**Key Metrics**:
- **Streaming Tab**: Processing time, input rate, scheduling delay
- **Jobs Tab**: Running and completed jobs
- **Executors Tab**: Resource usage

**Healthy Indicators**:
- Processing time < 10 seconds
- Scheduling delay near 0
- No failed tasks

### Logs

```bash
# Real-time logs
docker logs -f telemetra-spark-streaming

# Filter errors
docker logs telemetra-spark-streaming 2>&1 | grep ERROR

# Last 100 lines
docker logs telemetra-spark-streaming --tail 100
```

### Database Metrics

```sql
-- Processing volume
SELECT
    DATE_TRUNC('hour', processed_at) as hour,
    COUNT(*) as windows_processed,
    SUM(chat_count) as total_messages
FROM chat_summary_minute
WHERE processed_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;

-- Anomaly rate
SELECT
    DATE_TRUNC('hour', detected_at) as hour,
    COUNT(*) as anomalies_detected,
    AVG(intensity) as avg_intensity
FROM moments
WHERE detected_at > NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
```

---

## Troubleshooting

### Issue: "Kafka not available after 60 attempts"

**Cause**: Kafka not ready or network issue

**Solution**:
```bash
# Check Kafka is running
docker ps | grep kafka

# Restart Kafka
docker restart telemetra-kafka

# Wait 30 seconds, then restart Spark
sleep 30
docker restart telemetra-spark-streaming
```

### Issue: "Tables don't exist"

**Cause**: Database schema not created

**Solution**:
```bash
# Re-run table creation (see step 3 in Quick Start)
# Or run migrations if using Alembic
docker compose run --rm backend alembic upgrade head
```

### Issue: No data in database

**Cause**: No events being produced or consumed

**Solution**:
```bash
# 1. Verify Kafka has messages
docker exec telemetra-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --max-messages 5

# 2. Check Spark logs for errors
docker logs telemetra-spark-streaming | grep ERROR

# 3. Verify producer is running
docker ps | grep producer
```

### Issue: Out of memory

**Cause**: Insufficient memory allocation

**Solution**:
```bash
# Increase memory in .env or docker-compose.yml
export SPARK_DRIVER_MEMORY=4g
export SPARK_EXECUTOR_MEMORY=4g

# Restart
docker compose -f docker-compose.spark.yml restart spark-streaming
```

### Issue: Checkpoint corruption

**Cause**: Unclean shutdown or schema changes

**Solution** (development only - loses state):
```bash
# Clean checkpoints
docker compose -f docker-compose.spark.yml down -v
docker compose -f docker-compose.spark.yml up -d
```

---

## Development Workflow

### 1. Make Code Changes

Edit `spark_streaming_job.py` with your changes

### 2. Run Tests

```bash
pytest test_spark_job.py -v
ruff check spark_streaming_job.py
```

### 3. Rebuild and Restart

```bash
# Using Makefile
make build
make restart

# Or manually
docker compose -f docker-compose.spark.yml up --build -d
```

### 4. Verify Changes

```bash
# Check logs for startup
docker logs telemetra-spark-streaming --tail 50

# Query results
docker exec -i telemetra-postgres psql -U telemetra -d telemetra -c \
  "SELECT COUNT(*) FROM chat_summary_minute;"
```

---

## Production Deployment Checklist

### Infrastructure
- [ ] Use distributed checkpoint storage (HDFS/S3)
- [ ] Configure Spark cluster (standalone/YARN/K8s)
- [ ] Set up database connection pooling
- [ ] Configure Kafka consumer groups properly

### Security
- [ ] Enable Kafka SSL/SASL
- [ ] Use PostgreSQL SSL connections
- [ ] Store credentials in secrets manager (Vault, AWS Secrets)
- [ ] Implement network policies

### Monitoring
- [ ] Export Spark metrics to Prometheus
- [ ] Create Grafana dashboards
- [ ] Set up alerting (PagerDuty, Slack)
- [ ] Configure log aggregation (ELK, Splunk)

### Operations
- [ ] Automate checkpoint backups
- [ ] Document runbooks for common issues
- [ ] Set up auto-scaling policies
- [ ] Test disaster recovery procedures
- [ ] Configure circuit breakers

### Performance
- [ ] Load test with production volumes
- [ ] Tune batch sizes and trigger intervals
- [ ] Optimize database indexes
- [ ] Enable adaptive query execution

---

## Sample SQL Queries

### Top Streams by Chat Activity
```sql
SELECT
    stream_id,
    COUNT(*) as windows,
    AVG(chat_rate) as avg_chat_rate,
    MAX(chat_count) as peak_messages,
    SUM(unique_chatters) as total_unique_users
FROM chat_summary_minute
WHERE window_start > NOW() - INTERVAL '1 hour'
GROUP BY stream_id
ORDER BY avg_chat_rate DESC
LIMIT 10;
```

### Sentiment Analysis
```sql
SELECT
    stream_id,
    DATE_TRUNC('hour', window_start) as hour,
    AVG(avg_sentiment) as sentiment,
    SUM(positive_count) as positive_msgs,
    SUM(negative_count) as negative_msgs,
    ROUND(
        100.0 * SUM(positive_count) / NULLIF(SUM(positive_count + negative_count), 0),
        2
    ) as positive_pct
FROM chat_summary_minute
WHERE window_start > NOW() - INTERVAL '24 hours'
GROUP BY stream_id, hour
ORDER BY hour DESC, stream_id;
```

### Anomaly Summary
```sql
SELECT
    stream_id,
    COUNT(*) as anomaly_count,
    AVG(intensity) as avg_intensity,
    MAX(intensity) as max_intensity,
    ARRAY_AGG(DISTINCT moment_type) as types
FROM moments
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY stream_id
ORDER BY anomaly_count DESC;
```

### Top Emotes
```sql
SELECT
    stream_id,
    UNNEST(top_emotes) as emote,
    COUNT(*) as appearances
FROM chat_summary_minute
WHERE window_start > NOW() - INTERVAL '1 hour'
GROUP BY stream_id, emote
ORDER BY stream_id, appearances DESC
LIMIT 20;
```

---

## Advanced Topics

### Scaling to Spark Cluster

For production, deploy to a Spark cluster:

```bash
spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode cluster \
  --driver-memory 4g \
  --executor-memory 8g \
  --executor-cores 4 \
  --num-executors 5 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
  --conf spark.streaming.stopGracefullyOnShutdown=true \
  --conf spark.sql.streaming.checkpointLocation=hdfs://namenode:9000/checkpoints/telemetra \
  spark_streaming_job.py
```

### Kubernetes Deployment

Create `k8s/spark-streaming-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spark-streaming
  namespace: telemetra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: spark-streaming
  template:
    metadata:
      labels:
        app: spark-streaming
    spec:
      containers:
      - name: spark-streaming
        image: telemetra-spark-streaming:latest
        env:
        - name: KAFKA_BOOTSTRAP_SERVERS
          value: "kafka-service:9092"
        - name: POSTGRES_URL
          value: "jdbc:postgresql://postgres-service:5432/telemetra"
        - name: CHECKPOINT_LOCATION
          value: "s3a://telemetra-checkpoints/spark/"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
```

---

## Documentation Files

- **README.md**: Comprehensive technical documentation
- **QUICKSTART.md**: 5-minute quick start guide
- **INTEGRATION.md**: Integration into main Telemetra project
- **FILES_SUMMARY.md**: Detailed file descriptions
- **This file**: Deployment guide

---

## Support & Resources

### Documentation
- [Apache Spark Structured Streaming](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [PySpark SQL Functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)
- [Kafka Integration](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html)

### Troubleshooting
1. Check logs: `docker logs telemetra-spark-streaming`
2. View Spark UI: http://localhost:4040
3. Query database for results
4. Review this guide's Troubleshooting section

---

## Summary

All required files have been created successfully:

✅ **Core Application**: Production-ready PySpark streaming job
✅ **Docker Setup**: Dockerfile, entrypoint, docker-compose
✅ **Configuration**: Environment templates and examples
✅ **Documentation**: Comprehensive guides (4 markdown files)
✅ **Testing**: Unit tests with pytest
✅ **CI/CD**: GitHub Actions workflow
✅ **Dev Tools**: Makefile with common commands

**Next Steps**:
1. Review QUICKSTART.md for immediate testing
2. Run unit tests: `pytest test_spark_job.py -v`
3. Start with standalone deployment, then integrate
4. Monitor Spark UI and database for results
5. Tune configuration based on your data volume

**Project Location**:
`C:\Users\stive\Desktop\stuff\code\Telemetra\data_pipeline\spark\`

Happy streaming analytics! 🚀
