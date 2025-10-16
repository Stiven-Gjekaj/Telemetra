# Telemetra Spark Streaming Job

Real-time analytics pipeline for processing Twitch-like streaming platform events using Apache Spark Structured Streaming.

## Overview

This PySpark application implements a production-ready streaming analytics pipeline that:

- **Consumes** real-time events from Kafka topics (chat messages, viewer counts)
- **Processes** with windowed aggregations and watermarking for late data handling
- **Enriches** data with sentiment analysis using lexicon-based scoring
- **Detects** anomalies in chat activity using statistical z-score method
- **Writes** aggregated metrics and detected moments to PostgreSQL

## Architecture

```
Kafka Topics                Spark Streaming              PostgreSQL
├─ chat events    ─┐       ┌──────────────────┐       ┌─────────────────┐
│  (JSON)          ├──────→│ Windowed Aggs    │──────→│ chat_summary    │
│                  │       │ (1m, slide 10s)  │       │   _minute       │
├─ viewer events  ─┘       ├──────────────────┤       ├─────────────────┤
   (JSON)                  │ Sentiment        │       │                 │
                           │   Enrichment     │       │                 │
                           ├──────────────────┤       │                 │
                           │ Z-Score Anomaly  │──────→│ moments         │
                           │   Detection      │       │                 │
                           └──────────────────┘       └─────────────────┘
```

## Features

### 1. Windowed Aggregations
- **Window**: 1-minute tumbling windows with 10-second slide
- **Watermark**: 10-second tolerance for late-arriving data
- **Metrics Computed**:
  - `chat_count`: Total messages per window
  - `unique_chatters`: Distinct user count
  - `avg_sentiment`: Average sentiment score (-1.0 to 1.0)
  - `top_emotes`: Most frequently used emotes (array)
  - `chat_rate`: Messages per second
  - `avg_viewers`: Average concurrent viewers
  - `positive_count` / `negative_count`: Message sentiment distribution

### 2. Sentiment Analysis
Simple lexicon-based approach using predefined word lists:
- **Positive words**: love, great, awesome, pog, lol, etc.
- **Negative words**: hate, bad, cringe, fail, etc.
- **Score**: (positive_count - negative_count) / total_matched

### 3. Anomaly Detection
Statistical z-score method for chat activity spikes:
- **Method**: Rolling window z-score calculation
- **Window**: Last 10 time windows per stream
- **Formula**: `z = (value - mean) / stddev`
- **Threshold**: Configurable (default: 3.0 standard deviations)
- **Output**: Flagged moments written to `moments` table

### 4. Database Schema

#### chat_summary_minute
```sql
CREATE TABLE chat_summary_minute (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    chat_count INTEGER,
    unique_chatters INTEGER,
    avg_sentiment DOUBLE PRECISION,
    positive_count INTEGER,
    negative_count INTEGER,
    chat_rate DOUBLE PRECISION,
    avg_viewers DOUBLE PRECISION,
    top_emotes TEXT[],
    z_score DOUBLE PRECISION,
    is_anomaly BOOLEAN,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### moments
```sql
CREATE TABLE moments (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    moment_type VARCHAR(50) NOT NULL,
    description TEXT,
    intensity DOUBLE PRECISION,
    metadata JSONB,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker addresses |
| `POSTGRES_URL` | `jdbc:postgresql://postgres:5432/telemetra` | JDBC connection URL |
| `POSTGRES_USER` | `telemetra` | Database username |
| `POSTGRES_PASSWORD` | `telemetra` | Database password |
| `CHECKPOINT_LOCATION` | `/tmp/spark-checkpoints` | Streaming checkpoint dir |
| `ANOMALY_THRESHOLD` | `3.0` | Z-score threshold for anomalies |
| `SPARK_MASTER` | `local[*]` | Spark master URL |
| `SPARK_DRIVER_MEMORY` | `2g` | Driver memory allocation |
| `SPARK_EXECUTOR_MEMORY` | `2g` | Executor memory allocation |
| `SPARK_EXECUTOR_CORES` | `2` | CPU cores per executor |

## Running the Job

### Option 1: Docker Compose (Recommended)

Add to your `docker-compose.yml`:

```yaml
services:
  spark-streaming:
    build:
      context: ./data_pipeline/spark
      dockerfile: Dockerfile
    container_name: telemetra-spark-streaming
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - POSTGRES_URL=jdbc:postgresql://postgres:5432/telemetra
      - POSTGRES_USER=telemetra
      - POSTGRES_PASSWORD=telemetra
      - CHECKPOINT_LOCATION=/tmp/spark-checkpoints
      - ANOMALY_THRESHOLD=3.0
    depends_on:
      - kafka
      - postgres
    volumes:
      - spark-checkpoints:/tmp/spark-checkpoints
      - spark-events:/tmp/spark-events
    ports:
      - "4040:4040"  # Spark UI
    restart: unless-stopped
    networks:
      - telemetra-network

volumes:
  spark-checkpoints:
  spark-events:
```

Start the service:
```bash
docker compose up spark-streaming --build
```

### Option 2: Local spark-submit

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export POSTGRES_URL=jdbc:postgresql://localhost:5432/telemetra
export POSTGRES_USER=telemetra
export POSTGRES_PASSWORD=telemetra
export CHECKPOINT_LOCATION=/tmp/spark-checkpoints
```

3. **Run with spark-submit**:
```bash
spark-submit \
  --master local[*] \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
  spark_streaming_job.py
```

### Option 3: Spark Cluster Deployment

For production deployment to a Spark cluster:

```bash
spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode cluster \
  --driver-memory 4g \
  --executor-memory 4g \
  --executor-cores 4 \
  --num-executors 3 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
  --conf spark.streaming.stopGracefullyOnShutdown=true \
  --conf spark.sql.streaming.checkpointLocation=hdfs://namenode:9000/checkpoints/telemetra \
  spark_streaming_job.py
```

## Monitoring

### Spark UI
Access the Spark Web UI at: `http://localhost:4040`

Features:
- **Jobs**: View running and completed jobs
- **Stages**: Task-level execution details
- **Streaming**: Batch processing times, input rates
- **Environment**: Configuration and system properties

### Logs
View streaming job logs:
```bash
# Docker
docker logs -f telemetra-spark-streaming

# Kubernetes
kubectl logs -f deployment/spark-streaming -n telemetra
```

### Metrics
Key metrics to monitor:
- **Processing Time**: Should be < 10 seconds per batch
- **Input Rate**: Messages per second from Kafka
- **Scheduling Delay**: Indicates backpressure
- **Records Written**: Successful writes to PostgreSQL

## Development

### Testing Locally

1. **Start dependencies**:
```bash
docker compose -f infra/docker-compose.yml up kafka postgres -d
```

2. **Run mock producer**:
```bash
python data_pipeline/producer/twitch_mock_producer.py
```

3. **Run streaming job**:
```bash
python spark_streaming_job.py
```

4. **Query results**:
```sql
-- View aggregated metrics
SELECT * FROM chat_summary_minute ORDER BY window_start DESC LIMIT 10;

-- View detected anomalies
SELECT * FROM moments WHERE moment_type = 'chat_spike' ORDER BY timestamp DESC;
```

### Code Structure

```
spark_streaming_job.py
├── TelemetraStreamingJob (main class)
│   ├── __init__()                    # Load configuration
│   ├── create_spark_session()        # Initialize Spark
│   ├── read_kafka_stream()           # Kafka source
│   ├── enrich_with_sentiment()       # Sentiment scoring
│   ├── aggregate_chat_metrics()      # Chat windowing
│   ├── aggregate_viewer_metrics()    # Viewer windowing
│   ├── join_metrics()                # Combine streams
│   ├── detect_anomalies()            # Z-score detection
│   ├── prepare_summary_output()      # Format for DB
│   ├── prepare_moments_output()      # Extract anomalies
│   ├── write_to_postgres()           # JDBC sink
│   └── run()                         # Main execution
└── main()                            # Entry point
```

## Troubleshooting

### Common Issues

#### 1. Kafka Connection Failed
```
ERROR: Kafka not available after 60 attempts
```
**Solution**: Ensure Kafka is running and accessible:
```bash
docker ps | grep kafka
nc -zv localhost 9092
```

#### 2. Out of Memory Error
```
java.lang.OutOfMemoryError: Java heap space
```
**Solution**: Increase memory allocation:
```bash
export SPARK_DRIVER_MEMORY=4g
export SPARK_EXECUTOR_MEMORY=4g
```

#### 3. Checkpoint Recovery Failed
```
ERROR: Unable to recover from checkpoint
```
**Solution**: Clear checkpoint directory (development only):
```bash
docker exec telemetra-spark-streaming rm -rf /tmp/spark-checkpoints/*
```

#### 4. JDBC Write Errors
```
ERROR: Failed to write batch to chat_summary_minute
```
**Solution**:
- Verify PostgreSQL tables exist (run migrations)
- Check database credentials
- Ensure PostgreSQL has sufficient connections

### Performance Tuning

#### Increase Throughput
```python
.option("maxOffsetsPerTrigger", 100000)  # Increase batch size
.trigger(processingTime="5 seconds")      # Faster micro-batches
```

#### Reduce Latency
```python
.option("maxOffsetsPerTrigger", 1000)    # Smaller batches
.trigger(processingTime="1 second")       # Near real-time
```

#### Handle Backpressure
```bash
--conf spark.streaming.backpressure.enabled=true
--conf spark.streaming.kafka.maxRatePerPartition=1000
```

## Production Considerations

### 1. Checkpointing
- Use distributed storage (HDFS/S3) for checkpoints
- Regular cleanup of old checkpoint data
- Test recovery procedures

### 2. Resource Allocation
- Monitor CPU and memory usage
- Adjust executor count based on throughput
- Use dynamic allocation for variable load

### 3. Error Handling
- Configure dead letter queues for failed records
- Set up alerting for processing delays
- Implement circuit breakers for database failures

### 4. Security
- Use SSL for Kafka connections
- Encrypt database credentials (Vault, AWS Secrets Manager)
- Enable Spark authentication and encryption

### 5. Monitoring & Alerting
- Set up Prometheus metrics export
- Create Grafana dashboards
- Configure alerts for:
  - Processing delays > 30 seconds
  - Failed batches
  - Database connection issues
  - Anomaly detection rate

## References

- [Spark Structured Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Kafka Integration Guide](https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html)
- [PySpark SQL Functions](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/functions.html)

## License

MIT License - See LICENSE file for details
