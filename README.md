# Telemetra

Real-time Twitch analytics platform powered by Apache Kafka, Spark Structured Streaming, PostgreSQL, Redis, FastAPI, and React.

## Run Checklist

Get the system running in 3 commands:

```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Start all services with Docker Compose
docker compose up --build

# 3. Access the dashboard
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Spark Master UI: http://localhost:8080
```

The system will automatically:
- Initialize Kafka topics
- Create PostgreSQL database schema
- Start mock Twitch event producer
- Begin Spark streaming aggregations
- Serve real-time dashboard with WebSocket updates

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
- [Services](#services)
- [Runbook](#runbook)
- [Sample Analytics Queries](#sample-analytics-queries)
- [Troubleshooting](#troubleshooting)
- [Developer Notes](#developer-notes)

---

## Overview

Telemetra is a real-time analytics platform for Twitch streams that processes live events, detects anomalies, and provides interactive visualizations. The system demonstrates production-grade streaming architecture with:

- **Real-time event processing** via Apache Kafka
- **Windowed aggregations** using Spark Structured Streaming
- **Low-latency API** with FastAPI and Redis caching
- **Live dashboard** with React, D3.js, and WebSocket updates
- **Anomaly detection** using z-score statistical analysis
- **Sentiment analysis** with lexicon-based approach

**Use Cases:**
- Monitor viewer engagement in real-time
- Detect unusual chat activity or viewer spikes
- Track top chatters, emotes, and viewer trends
- Analyze sentiment and toxicity patterns

---

## Architecture

```mermaid
graph TB
    subgraph "Data Ingestion"
        Producer[Mock Twitch Producer<br/>Python]
    end

    subgraph "Event Streaming"
        Kafka[Apache Kafka<br/>Topics: chat, viewer, transactions,<br/>stream_meta, derived.sentiment]
        Zookeeper[Zookeeper<br/>Coordination]
    end

    subgraph "Stream Processing"
        SparkMaster[Spark Master]
        SparkWorker[Spark Worker<br/>2G RAM, 2 cores]
        SparkStreaming[Spark Streaming Job<br/>Windowed Aggregations<br/>Anomaly Detection]
    end

    subgraph "Data Layer"
        Postgres[(PostgreSQL<br/>streams, chat_summary_minute,<br/>viewer_timeseries, transactions,<br/>moments)]
        Redis[(Redis Cache<br/>256MB LRU<br/>Top chatters, recent metrics)]
    end

    subgraph "API & Frontend"
        Backend[FastAPI Backend<br/>REST + WebSocket<br/>Port 8000]
        Frontend[React + D3.js Frontend<br/>Live Dashboard<br/>Port 3000]
    end

    Producer -->|Produce Events| Kafka
    Kafka -.->|Coordinate| Zookeeper
    Kafka -->|Stream| SparkStreaming
    SparkMaster -->|Manage| SparkWorker
    SparkStreaming -->|Submit to| SparkMaster
    SparkStreaming -->|Write Aggregates| Postgres
    SparkStreaming -->|Write Anomalies| Postgres
    Backend -->|Query| Postgres
    Backend -->|Cache| Redis
    Backend -->|Consume Events| Kafka
    Backend <-->|WebSocket| Frontend
    Frontend -->|HTTP| Backend

    style Producer fill:#e1f5ff
    style Kafka fill:#fff4e1
    style SparkStreaming fill:#ffe1f5
    style Postgres fill:#e1ffe1
    style Redis fill:#ffe1e1
    style Backend fill:#f5e1ff
    style Frontend fill:#e1e1ff
```

### Data Flow

1. **Producer** generates mock Twitch events (chat messages, viewer counts, transactions, stream metadata)
2. **Kafka** buffers events in topics with 24-hour retention
3. **Spark Streaming** consumes events, performs windowed aggregations (1-minute windows), detects anomalies using z-score analysis
4. **PostgreSQL** stores aggregated metrics, detected moments/anomalies, and raw transactions
5. **Redis** caches frequently accessed data (top chatters, recent viewer counts) with LRU eviction
6. **Backend** serves REST API endpoints and WebSocket connections for real-time updates
7. **Frontend** displays interactive D3.js visualizations with live data updates

---

## Features

### Real-Time Processing
- **1-minute windowed aggregations** for chat rate, viewer count, transaction volume
- **Watermarking** for late data handling (10-second threshold)
- **Anomaly detection** using z-score (threshold: 3.0) for chat spikes and viewer drops
- **Sentiment analysis** with lexicon-based scoring (placeholder for ML models)

### API Endpoints
- `GET /health` - Service health check
- `GET /streams` - List all tracked streams
- `GET /streams/{id}/metrics` - Historical metrics for a stream
- `GET /streams/{id}/moments` - Detected anomalies and moments
- `WS /live/{stream_id}` - WebSocket for real-time metric updates

### Dashboard Visualizations
- **Viewer Chart** - D3.js line chart with historical and live viewer counts
- **Chat Rate Chart** - Real-time chat message rate with anomaly highlights
- **Live Metrics** - Current viewer count, chat rate, transactions per minute
- **Moments List** - Timeline of detected anomalies with severity indicators

### Monitoring & Observability
- **Health checks** for all Docker Compose services
- **Spark UI** for job monitoring (port 8080)
- **FastAPI docs** with Swagger UI (port 8000/docs)

---

## Prerequisites

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Git** for cloning the repository
- **8GB RAM minimum** (Spark worker uses 2GB, Postgres/Kafka/Redis use additional memory)
- **Ports available**: 2181 (Zookeeper), 9092/29092 (Kafka), 5432 (Postgres), 6379 (Redis), 7077/8080 (Spark), 8000 (Backend), 3000 (Frontend)

---

## Quickstart

### 1. Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url> telemetra
cd telemetra

# Copy environment template
cp .env.example .env

# (Optional) Edit .env to customize configuration
# nano .env
```

### 2. Start All Services

```bash
# Build and start all containers
docker compose up --build

# Or run in detached mode
docker compose up --build -d
```

**Startup time**: ~2-3 minutes for all health checks to pass and services to be ready.

### 3. Access the System

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost:3000 | React app with live visualizations |
| **Backend API Docs** | http://localhost:8000/docs | Interactive Swagger UI |
| **Spark Master UI** | http://localhost:8080 | Spark job monitoring |
| **Kafka** | localhost:29092 | Kafka broker (external access) |
| **PostgreSQL** | localhost:5432 | Database (credentials in .env) |
| **Redis** | localhost:6379 | Cache |

### 4. Verify Data Flow

```bash
# Check producer is generating events
docker logs telemetra-producer --tail 50

# Check Spark is processing
docker logs telemetra-spark-streaming --tail 50

# Check backend is serving
curl http://localhost:8000/health

# Check metrics are being aggregated
curl http://localhost:8000/streams
```

### 5. Stop Services

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (WARNING: deletes all data)
docker compose down -v
```

---

## Services

### Zookeeper
- **Image**: confluentinc/cp-zookeeper:7.5.0
- **Port**: 2181
- **Purpose**: Kafka cluster coordination

### Kafka
- **Image**: confluentinc/cp-kafka:7.5.0
- **Ports**: 9092 (internal), 29092 (external)
- **Topics**: `twitch-events` (auto-created), `chat`, `viewer`, `transactions`, `stream_meta`, `derived.sentiment`
- **Retention**: 24 hours
- **Replication**: 1 (single broker for dev)

### PostgreSQL
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Database**: telemetra
- **User**: telemetra_user (see .env)
- **Schema**: Initialized from `backend/migrations/*.sql`
- **Tables**: `streams`, `chat_summary_minute`, `viewer_timeseries`, `transactions`, `moments`

### Redis
- **Image**: redis:7-alpine
- **Port**: 6379
- **Max Memory**: 256MB
- **Eviction**: allkeys-lru (evict least recently used keys)
- **Purpose**: Cache top chatters, recent metrics

### Spark Master
- **Image**: bitnami/spark:3.5.0
- **Ports**: 7077 (master RPC), 8080 (web UI)
- **Purpose**: Coordinate Spark workers and streaming jobs

### Spark Worker
- **Image**: bitnami/spark:3.5.0
- **Resources**: 2GB memory, 2 CPU cores
- **Purpose**: Execute Spark tasks

### Spark Streaming Job
- **Build**: Custom image from `spark/Dockerfile`
- **Script**: `spark_streaming_job.py`
- **Master**: spark://spark-master:7077
- **Input**: Kafka topics
- **Output**: PostgreSQL via JDBC
- **Features**: Windowed aggregations, watermarking, z-score anomaly detection

### Backend (FastAPI)
- **Build**: Custom image from `backend/Dockerfile`
- **Port**: 8000
- **Framework**: FastAPI with asyncpg, Redis, Kafka consumer
- **Health Check**: `GET /health`
- **API Docs**: http://localhost:8000/docs

### Frontend (React)
- **Build**: Custom image from `frontend/Dockerfile`
- **Port**: 3000
- **Framework**: React 18 + TypeScript + Vite
- **Visualizations**: D3.js charts
- **Real-time**: WebSocket connection to backend

### Producer (Mock Data)
- **Build**: Custom image from `producer/Dockerfile`
- **Script**: `twitch_mock_producer.py`
- **Interval**: 1 second (configurable via `PRODUCER_INTERVAL`)
- **Channels**: xqc, shroud, pokimane, ninja, summit1g (configurable via `MOCK_CHANNELS`)
- **Events**: Generates chat messages, viewer counts, transactions, stream metadata

---

## Runbook

### Common Operations

#### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f spark-streaming
docker compose logs -f producer

# Last 100 lines
docker compose logs --tail 100 kafka
```

#### Restart a Service
```bash
# Restart backend only
docker compose restart backend

# Rebuild and restart frontend
docker compose up --build -d frontend
```

#### Access Service Shell
```bash
# PostgreSQL shell
docker exec -it telemetra-postgres psql -U telemetra_user -d telemetra

# Backend shell
docker exec -it telemetra-backend bash

# Kafka shell
docker exec -it telemetra-kafka bash
```

#### Check Service Health
```bash
# All health checks
docker compose ps

# Backend health endpoint
curl http://localhost:8000/health

# Kafka broker status
docker exec telemetra-kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# PostgreSQL connection
docker exec telemetra-postgres pg_isready -U telemetra_user
```

#### Kafka Operations
```bash
# List topics
docker exec telemetra-kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe topic
docker exec telemetra-kafka kafka-topics --describe --topic twitch-events --bootstrap-server localhost:9092

# Consume messages (last 10)
docker exec telemetra-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic twitch-events \
  --from-beginning \
  --max-messages 10

# Check consumer group lag
docker exec telemetra-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group spark-streaming-consumer
```

#### Database Operations
```bash
# Connect to PostgreSQL
docker exec -it telemetra-postgres psql -U telemetra_user -d telemetra

# Backup database
docker exec telemetra-postgres pg_dump -U telemetra_user telemetra > backup.sql

# Restore database
cat backup.sql | docker exec -i telemetra-postgres psql -U telemetra_user -d telemetra

# Run migration manually
docker exec -i telemetra-postgres psql -U telemetra_user -d telemetra < backend/migrations/001_init_schema.sql
```

#### Redis Operations
```bash
# Connect to Redis CLI
docker exec -it telemetra-redis redis-cli

# Check cache keys
docker exec telemetra-redis redis-cli KEYS '*'

# Get cached value
docker exec telemetra-redis redis-cli GET top_chatters:stream_1

# Clear cache
docker exec telemetra-redis redis-cli FLUSHALL
```

#### Monitor Resource Usage
```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean up unused resources
docker system prune -a
```

#### Scale Services
```bash
# Scale Spark workers
docker compose up -d --scale spark-worker=3

# Note: Kafka replication factor is 1, so scaling kafka requires config changes
```

---

## Sample Analytics Queries

Connect to PostgreSQL:
```bash
docker exec -it telemetra-postgres psql -U telemetra_user -d telemetra
```

### Top Chatters (Last Hour)
```sql
SELECT
    username,
    COUNT(*) as message_count
FROM chat_summary_minute
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY username
ORDER BY message_count DESC
LIMIT 10;
```

### Top Emotes (Last 24 Hours)
```sql
SELECT
    emote,
    COUNT(*) as usage_count
FROM chat_summary_minute
WHERE
    timestamp > NOW() - INTERVAL '24 hours'
    AND emote IS NOT NULL
GROUP BY emote
ORDER BY usage_count DESC
LIMIT 20;
```

### Viewer Trends (Hourly Average)
```sql
SELECT
    DATE_TRUNC('hour', timestamp) as hour,
    stream_id,
    AVG(viewer_count) as avg_viewers,
    MAX(viewer_count) as peak_viewers,
    MIN(viewer_count) as min_viewers
FROM viewer_timeseries
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY hour, stream_id
ORDER BY hour DESC;
```

### Detected Anomalies (Recent)
```sql
SELECT
    timestamp,
    stream_id,
    moment_type,
    description,
    severity,
    metadata
FROM moments
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC
LIMIT 50;
```

### Chat Activity by Hour of Day
```sql
SELECT
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    AVG(message_count) as avg_messages,
    COUNT(*) as sample_count
FROM chat_summary_minute
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY hour_of_day
ORDER BY hour_of_day;
```

### Revenue by Stream (Transactions)
```sql
SELECT
    stream_id,
    COUNT(*) as transaction_count,
    SUM(amount) as total_revenue,
    AVG(amount) as avg_transaction
FROM transactions
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY stream_id
ORDER BY total_revenue DESC;
```

### Sentiment Distribution
```sql
SELECT
    stream_id,
    CASE
        WHEN sentiment_score > 0.5 THEN 'Positive'
        WHEN sentiment_score < -0.5 THEN 'Negative'
        ELSE 'Neutral'
    END as sentiment_category,
    COUNT(*) as count
FROM chat_summary_minute
WHERE
    timestamp > NOW() - INTERVAL '24 hours'
    AND sentiment_score IS NOT NULL
GROUP BY stream_id, sentiment_category
ORDER BY stream_id, sentiment_category;
```

---

## Troubleshooting

### Services Won't Start

**Symptom**: `docker compose up` fails or services restart repeatedly

**Solutions**:
1. Check port availability:
   ```bash
   # Check if ports are in use
   netstat -an | grep -E '(3000|8000|5432|6379|9092|2181|7077|8080)'
   ```
2. Check Docker resources (need 8GB+ RAM):
   ```bash
   docker system info | grep -E '(Memory|CPUs)'
   ```
3. Review logs for specific service:
   ```bash
   docker compose logs kafka
   docker compose logs postgres
   ```
4. Increase health check timeout in docker-compose.yml if services are slow to start

### Kafka Connection Errors

**Symptom**: Producer or Spark job can't connect to Kafka

**Solutions**:
1. Wait for Kafka health check to pass:
   ```bash
   docker compose ps kafka
   # Should show "healthy" status
   ```
2. Verify Kafka is listening:
   ```bash
   docker exec telemetra-kafka kafka-broker-api-versions --bootstrap-server localhost:9092
   ```
3. Check Zookeeper is running:
   ```bash
   docker compose ps zookeeper
   ```
4. Restart Kafka and dependent services:
   ```bash
   docker compose restart zookeeper kafka
   docker compose restart spark-streaming producer
   ```

### Database Connection Errors

**Symptom**: Backend can't connect to PostgreSQL

**Solutions**:
1. Verify PostgreSQL is ready:
   ```bash
   docker exec telemetra-postgres pg_isready -U telemetra_user
   ```
2. Check database exists:
   ```bash
   docker exec telemetra-postgres psql -U telemetra_user -l
   ```
3. Verify credentials in .env match docker-compose.yml:
   ```bash
   cat .env | grep POSTGRES
   ```
4. Check migrations ran successfully:
   ```bash
   docker compose logs postgres | grep -i migration
   ```

### Spark Job Not Processing

**Symptom**: No data appearing in PostgreSQL, Spark logs show errors

**Solutions**:
1. Check Spark Master UI: http://localhost:8080
   - Verify worker is connected
   - Check application status
2. Review Spark streaming logs:
   ```bash
   docker compose logs spark-streaming --tail 200
   ```
3. Verify Kafka topics have data:
   ```bash
   docker exec telemetra-kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic twitch-events \
     --from-beginning \
     --max-messages 5
   ```
4. Check PostgreSQL JDBC connection from Spark container:
   ```bash
   docker exec telemetra-spark-streaming nc -zv postgres 5432
   ```

### WebSocket Connection Fails

**Symptom**: Frontend shows "Disconnected" or can't connect to WebSocket

**Solutions**:
1. Verify backend is healthy:
   ```bash
   curl http://localhost:8000/health
   ```
2. Check backend logs for WebSocket errors:
   ```bash
   docker compose logs backend | grep -i websocket
   ```
3. Test WebSocket manually:
   ```bash
   # Using wscat (npm install -g wscat)
   wscat -c ws://localhost:8000/live/stream_1
   ```
4. Check CORS configuration in backend environment:
   ```bash
   docker compose config | grep CORS
   ```

### No Data in Dashboard

**Symptom**: Frontend loads but shows empty charts

**Solutions**:
1. Verify producer is running:
   ```bash
   docker compose logs producer --tail 50
   ```
2. Check data exists in PostgreSQL:
   ```bash
   docker exec -it telemetra-postgres psql -U telemetra_user -d telemetra \
     -c "SELECT COUNT(*) FROM viewer_timeseries;"
   ```
3. Verify backend API returns data:
   ```bash
   curl http://localhost:8000/streams
   ```
4. Check browser console for frontend errors (F12 → Console)

### High Memory Usage

**Symptom**: System runs out of memory, services crash

**Solutions**:
1. Reduce Spark worker memory in docker-compose.yml:
   ```yaml
   SPARK_WORKER_MEMORY=1G  # Down from 2G
   ```
2. Reduce Redis max memory:
   ```yaml
   command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru
   ```
3. Limit Kafka log retention:
   ```yaml
   KAFKA_LOG_RETENTION_HOURS: 12  # Down from 24
   ```
4. Stop unused services:
   ```bash
   docker compose stop spark-master spark-worker
   # (This will stop Spark processing but other services continue)
   ```

### Container Build Fails

**Symptom**: `docker compose up --build` fails during image build

**Solutions**:
1. Check Docker disk space:
   ```bash
   docker system df
   ```
2. Clean up old images and containers:
   ```bash
   docker system prune -a
   ```
3. Build services individually to isolate issue:
   ```bash
   docker compose build backend
   docker compose build frontend
   docker compose build producer
   docker compose build spark-streaming
   ```
4. Check Dockerfile syntax in the failing service directory

---

## Developer Notes

### Code Locations

**Core Data Pipeline**:
- Producer: `producer/twitch_mock_producer.py` or `data_pipeline/producer/twitch_mock_producer.py`
- Spark Job: `spark/streaming_job.py` or `data_pipeline/spark/spark_streaming_job.py`
  - Windowed aggregations: Lines ~80-150
  - Z-score anomaly detection: Lines ~200-250
  - Sentiment analysis (lexicon): Lines ~300-350

**Backend API**:
- Main app: `backend/app/main.py`
- Stream routes: `backend/app/routes/streams.py`
- Metrics routes: `backend/app/routes/metrics.py`
- WebSocket manager: `backend/app/services/websocket_manager.py`
- Kafka consumer: `backend/app/services/kafka_consumer.py`
- Database layer: `backend/app/database.py`
- Redis cache: `backend/cache.py`

**Frontend Dashboard**:
- Main app: `frontend/src/App.tsx`
- Dashboard: `frontend/src/components/Dashboard.tsx`
- Viewer chart: `frontend/src/components/charts/ViewerChart.tsx`
- Chat rate chart: `frontend/src/components/charts/ChatRateChart.tsx`
- WebSocket service: `frontend/src/services/websocket.ts`
- API service: `frontend/src/services/api.ts`

**Database**:
- Schema: `postgres/init.sql`
- Migrations: `backend/migrations/*.sql`

**Infrastructure**:
- Docker Compose: `docker-compose.yml` (root level)
- Environment template: `.env.example`

### Future Stretch Tasks

**Short-term Enhancements**:
1. Add unit tests for backend endpoints (pytest)
2. Add integration tests for full data pipeline
3. Create GitHub Actions CI/CD workflow
4. Add Prometheus + Grafana monitoring dashboards
5. Implement proper Alembic database migrations
6. Add API rate limiting and authentication
7. Create Makefile for common operations

**Medium-term Features**:
1. Real Twitch API integration (replace mock producer)
2. ML-based sentiment analysis (replace lexicon fallback)
   - Placeholder code: `spark/streaming_job.py:300-350`
3. Advanced anomaly detection (LSTM, isolation forest)
   - Placeholder code: `spark/streaming_job.py:200-250`
4. Emote frequency tracking and trending emotes
5. Clip moment detection (viewership spikes correlating with clips)
6. Multi-stream comparison dashboard
7. Historical trend analysis and predictions

**Long-term Infrastructure**:
1. Kubernetes manifests for production deployment (see `deploy/k8s/`)
2. Horizontal scaling for Spark workers and backend
3. Kafka cluster with replication (multi-broker)
4. Database read replicas for analytics queries
5. CDN integration for frontend
6. Apache Flink as alternative to Spark
7. GraphQL API layer for complex queries
8. Real-time alerting (PagerDuty, Slack webhooks)

### Technology Choices

**Why Kafka**: High-throughput event streaming, decouples producers/consumers, supports replay

**Why Spark Streaming**: Native Kafka integration, windowed aggregations, stateful processing, JDBC sinks

**Why PostgreSQL**: Structured data, ACID guarantees, analytical queries, widely supported

**Why Redis**: Sub-millisecond latency for hot data, LRU eviction for bounded memory

**Why FastAPI**: Async support, WebSocket, auto-generated docs, high performance

**Why React + D3**: Component-based UI, rich visualizations, real-time updates via WebSocket

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Follow existing code style (Black for Python, Prettier for TypeScript)
4. Add tests for new features
5. Update documentation
6. Submit pull request

### License

[Specify your license here]

### Contact

[Add contact information or links]

---

**Built with ❤️ for real-time data enthusiasts**
