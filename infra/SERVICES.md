# Telemetra Services Reference

Quick reference guide for all services in the Telemetra MVP infrastructure.

## Service Overview

### By Tier

#### Infrastructure (Message Queue & Storage)
| Service | Port | Role | Health Check |
|---------|------|------|--------------|
| Zookeeper | 2181 | Kafka coordination | TCP 2181 |
| Kafka | 9092 | Event streaming | Broker API |
| PostgreSQL | 5432 | Data storage | `pg_isready` |
| Redis | 6379 | Caching | PING |

#### Processing (Compute & Aggregation)
| Service | Ports | Role | Health Check |
|---------|-------|------|--------------|
| Spark Master | 7077, 8080 | Job scheduler | curl port 8080 |
| Spark Worker | 8081 | Task execution | curl port 8081 |
| Mock Producer | - | Test data generation | Logs |
| Spark Streaming | - | Stream processing | Logs |

#### Application (API & UI)
| Service | Port | Role | Health Check |
|---------|------|------|--------------|
| Backend (FastAPI) | 8000 | REST API + WebSocket | GET /health |
| Frontend (React) | 3000 | Web dashboard | HTTP 200 |

#### Optional (Monitoring)
| Service | Port | Role | Profile |
|---------|------|------|---------|
| Kafka UI | 8888 | Topic monitoring | `full` |
| pgAdmin | 5050 | Database UI | `full` |

## Service Details

### Zookeeper
**Docker Image**: `confluentinc/cp-zookeeper:7.5.0`
**Container**: `telemetra_zookeeper`
**Port**: 2181 (client connections)

**Purpose**: Coordination and configuration management for Kafka broker
- Maintains broker state
- Manages partition leadership
- Coordinates cluster operations

**Environment**:
```
ZOOKEEPER_CLIENT_PORT=2181
ZOOKEEPER_TICK_TIME=2000
ZOOKEEPER_SYNC_LIMIT=5
ZOOKEEPER_INIT_LIMIT=10
```

**Health Check**:
```bash
nc -z localhost 2181
docker compose exec zookeeper nc -z localhost 2181
```

**Dependencies**: None (starts first)

**Use Cases**:
- Kafka cluster starts here
- Never accessed directly by applications

---

### Kafka
**Docker Image**: `confluentinc/cp-kafka:7.5.0`
**Container**: `telemetra_kafka`
**Port**: 9092 (external), 29092 (internal)
**Topics**: 4 auto-created topics

**Purpose**: Distributed event streaming platform
- Produces: Mock producer writes events
- Consumers: Spark, backend services

**Key Topics**:
```
telemetra.events.chat           # Chat messages
telemetra.events.viewer         # Viewer counts
telemetra.events.transactions   # Purchase events
telemetra.events.stream_meta    # Stream metadata
```

**Environment**:
```
KAFKA_BROKER_ID=1
KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
KAFKA_AUTO_CREATE_TOPICS_ENABLE=true
KAFKA_LOG_RETENTION_HOURS=168  # 7 days
```

**Health Check**:
```bash
kafka-broker-api-versions.sh --bootstrap-server localhost:9092
docker compose exec kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```

**Dependencies**: Zookeeper

**Use Cases**:
- Producer writes test data
- Spark reads and processes
- Backend may consume for real-time updates

---

### PostgreSQL
**Docker Image**: `postgres:15-alpine`
**Container**: `telemetra_postgres`
**Port**: 5432
**Volume**: `telemetra_postgres_data`

**Purpose**: Primary database for analytics and reporting
- Aggregated metrics (1-minute windows)
- Time series data (viewer counts)
- Detected anomalies/moments
- Historical data

**Tables**:
```
streams                 # Stream metadata
chat_summary_minute    # Chat aggregates (main analytics table)
viewer_timeseries      # Viewer data points
transactions           # Financial events
moments                # Detected anomalies
```

**Credentials**:
```
User: telemetra (configurable)
Password: telemetra_dev_password (set in .env)
Database: telemetra
```

**Initialization**:
- `infra/init-db.sql` runs on first start
- Creates all tables, indexes, materialized views
- Pre-populates demo stream

**Health Check**:
```bash
pg_isready -U telemetra -d telemetra
docker compose exec postgres pg_isready -U telemetra -d telemetra
```

**Connection String**:
```
Internal: postgresql://telemetra:password@postgres:5432/telemetra
External: postgresql://telemetra:password@localhost:5432/telemetra
```

**Dependencies**: None (data layer)

**Use Cases**:
- Spark writes aggregated data
- Backend reads for REST endpoints
- Frontend fetches metrics via backend
- Historical analysis queries

---

### Redis
**Docker Image**: `redis:7-alpine`
**Container**: `telemetra_redis`
**Port**: 6379
**Volume**: `telemetra_redis_data`

**Purpose**: In-memory cache for real-time metrics
- Latest viewer count
- Latest chat rate
- Session data
- Hot metrics for WebSocket

**Persistence**:
```
RDB snapshots (appendonly.aof)
Kept for development reference, ephemeral in nature
```

**Health Check**:
```bash
redis-cli ping
docker compose exec redis redis-cli ping
```

**Connection String**:
```
redis://redis:6379
```

**Dependencies**: None (cache layer)

**Use Cases**:
- Backend caches latest aggregates
- WebSocket serves data from cache
- Real-time metrics updates
- Optional session storage

---

### Spark Master
**Docker Image**: `bitnami/spark:3.5.0`
**Container**: `telemetra_spark_master`
**Ports**: 7077 (RPC), 8080 (Web UI)

**Purpose**: Master node for distributed computing framework
- Receives job submissions
- Schedules work to workers
- Manages resources
- Provides Web UI for monitoring

**Configuration**:
```
SPARK_MODE=master
SPARK_RPC_AUTHENTICATION_ENABLED=false
SPARK_SSL_ENABLED=false
```

**Web UI**: http://localhost:8080
- View running jobs
- Monitor resource usage
- Check worker status

**Health Check**:
```bash
curl -f http://localhost:8080
docker compose exec spark-master curl -f http://localhost:8080
```

**Dependencies**: None (master starts first)

**Use Cases**:
- Spark streaming job submits here
- Coordinate distributed processing
- Monitor job execution

---

### Spark Worker
**Docker Image**: `bitnami/spark:3.5.0`
**Container**: `telemetra_spark_worker`
**Port**: 8081 (Web UI)

**Purpose**: Worker node for distributed computation
- Executes tasks assigned by master
- Processes partitions
- Manages resources

**Configuration**:
```
SPARK_MODE=worker
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_WORKER_MEMORY=1G     # 1GB per worker
SPARK_WORKER_CORES=2       # 2 cores per worker
```

**Web UI**: http://localhost:8081
- Task execution status
- Resource usage
- Executor logs

**Dependencies**: Spark Master

**Use Cases**:
- Processes streaming data
- Aggregates chat metrics
- Performs anomaly detection

---

### Mock Producer
**Docker Image**: Custom (from `data_pipeline/producer/Dockerfile`)
**Container**: `telemetra_mock_producer`

**Purpose**: Generates synthetic streaming data for testing
- Creates realistic chat messages
- Generates viewer count updates
- Produces transaction events
- Streams metadata

**Configuration**:
```
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
PRODUCER_RATE_PER_SEC=10           # 10 messages/sec (configurable)
PRODUCER_CHANNELS=demo_stream      # Stream to simulate
```

**Topics Written**:
```
telemetra.events.chat
telemetra.events.viewer
telemetra.events.transactions
telemetra.events.stream_meta
```

**Health Check**:
```bash
docker compose logs mock-producer | grep "produced\|sending"
```

**Dependencies**: Kafka

**Use Cases**:
- Development and testing
- Load testing (increase PRODUCER_RATE_PER_SEC)
- Demo data generation

---

### Spark Streaming Job
**Docker Image**: Custom (from `data_pipeline/spark/Dockerfile`)
**Container**: `telemetra_spark_streaming`

**Purpose**: Real-time stream processing
- Reads from Kafka topics
- Performs 1-minute windowed aggregations
- Detects anomalies (z-score)
- Enriches with sentiment analysis
- Writes results to PostgreSQL

**Configuration**:
```
SPARK_MASTER=spark://spark-master:7077
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
CHAT_WINDOW_DURATION_SECONDS=60
CHAT_WINDOW_SLIDE_SECONDS=10
ANOMALY_DETECTION_THRESHOLD=3.0
```

**Input**: Kafka topics (chat, viewer)

**Output**: PostgreSQL tables (aggregates, moments)

**Health Check**:
```bash
docker compose logs spark-streaming-job | grep "window\|aggregate\|written"
```

**Dependencies**: Spark Master, Kafka, PostgreSQL

**Use Cases**:
- Core analytics pipeline
- Real-time aggregations
- Anomaly detection
- Data enrichment

---

### Backend (FastAPI)
**Docker Image**: Custom (from `backend/Dockerfile`)
**Container**: `telemetra_backend`
**Port**: 8000

**Purpose**: REST API and WebSocket server
- Query aggregated metrics
- Stream live data via WebSocket
- Database queries
- Redis caching

**Key Endpoints**:
```
GET  /health              # Health check
GET  /docs               # Swagger documentation
GET  /streams            # List streams
GET  /streams/{id}       # Stream details
GET  /streams/{id}/metrics  # Aggregated metrics
GET  /streams/{id}/moments  # Anomalies/moments
WS   /live/{stream_id}   # WebSocket for live metrics
```

**Configuration**:
```
POSTGRES_HOST=postgres
REDIS_URL=redis://redis:6379
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
API_TITLE=Telemetra API
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DEBUG=false
```

**Health Check**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

**Dependencies**: PostgreSQL, Redis, Kafka

**Use Cases**:
- Frontend REST queries
- Live metrics streaming
- API clients
- Real-time dashboards

---

### Frontend (React)
**Docker Image**: Custom (from `frontend/Dockerfile`)
**Container**: `telemetra_frontend`
**Port**: 3000

**Purpose**: Web dashboard for real-time analytics
- Real-time metrics visualization
- WebSocket connection to backend
- Interactive components
- Live updates

**Components**:
- PulseBar: Animated viewer count
- ChatFlow: Chat rate visualization
- EmoteCloud: Top emotes bubble chart
- MomentsTimeline: Detected anomalies

**Configuration**:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

**Health Check**:
```bash
curl http://localhost:3000
# Expected: HTTP 200 with HTML
```

**Dependencies**: Backend

**Access**: http://localhost:3000

**Use Cases**:
- Real-time monitoring dashboard
- Live analytics viewing
- Moment detection visualization

---

## Optional Services

### Kafka UI
**Docker Image**: `provectuslabs/kafka-ui:latest`
**Container**: `telemetra_kafka_ui`
**Port**: 8888
**Profile**: `full` only

**Purpose**: Web UI for Kafka monitoring
- View topics
- Inspect messages
- Monitor consumer groups
- Topic statistics

**Access**: http://localhost:8888

**Start**:
```bash
docker compose --profile full --profile dev up -d
```

---

### pgAdmin
**Docker Image**: `dpage/pgadmin4:latest`
**Container**: `telemetra_pgadmin`
**Port**: 5050
**Profile**: `full` only

**Purpose**: PostgreSQL database administration UI
- Query builder
- Data browser
- Schema management
- Query execution

**Credentials**:
```
Email: admin@telemetra.local (configurable)
Password: admin (set in .env)
```

**Access**: http://localhost:5050

**Start**:
```bash
docker compose --profile full --profile dev up -d
```

---

## Service Startup Order

Automatic ordering via `depends_on` with `service_healthy` conditions:

```
1. PostgreSQL (starts first, data layer)
2. Redis (starts, cache layer)
3. Zookeeper (starts, Kafka coordination)
4. Kafka (depends on Zookeeper)
5. Spark Master (depends on none)
6. Spark Worker (depends on Spark Master)
7. Mock Producer (depends on Kafka)
8. Spark Streaming (depends on Spark Master, Kafka, PostgreSQL)
9. Backend (depends on PostgreSQL, Redis, Kafka)
10. Frontend (depends on Backend)
```

**Startup Time**: ~30-60 seconds for all services to be healthy

---

## Service Communication

### Internal Network (telemetra_network)
```
Mock Producer    → Kafka (tcp://kafka:29092)
Spark Streaming  → Kafka (tcp://kafka:29092)
                 → PostgreSQL (tcp://postgres:5432)
Spark Master     ← Worker (rpc://spark-worker:7078)
Backend          → PostgreSQL (tcp://postgres:5432)
                 → Redis (tcp://redis:6379)
                 → Kafka (tcp://kafka:29092)
Frontend         → Backend (http://backend:8000)
                 → Backend WebSocket (ws://backend:8000)
```

### Host Network (External)
```
Developer    → Frontend (http://localhost:3000)
            → Backend (http://localhost:8000)
            → Kafka UI (http://localhost:8888)
            → pgAdmin (http://localhost:5050)
            → Spark UI (http://localhost:8080)
```

---

## Performance Characteristics

| Service | CPU Limit | Memory Limit | Typical Usage |
|---------|-----------|--------------|--------------|
| Zookeeper | 0.5 | 512M | 50M |
| Kafka | 1.0 | 1G | 200-300M |
| PostgreSQL | 1.0 | 1G | 100-200M |
| Redis | 0.5 | 512M | 10-50M |
| Spark Master | 1.0 | 1.5G | 500M-1G |
| Spark Worker | 2.0 | 2G | 1-2G |
| Backend | 1.0 | 1G | 100-200M |
| Frontend | 0.5 | 512M | 50-100M |
| Mock Producer | 0.5 | 512M | 20-50M |
| Spark Streaming | 2.0 | 2G | 1-2G |

**Total (dev profile)**: ~12 CPU cores, 11.5GB memory

---

## Logging

Each service outputs logs to docker compose:

```bash
# All services
docker compose -f infra/docker-compose.yml logs

# Specific service
docker compose -f infra/docker-compose.yml logs -f backend

# Follow logs
docker compose -f infra/docker-compose.yml logs -f

# Last N lines
docker compose -f infra/docker-compose.yml logs --tail=100

# With timestamps
docker compose -f infra/docker-compose.yml logs --timestamps
```

---

## Environment Variables per Service

See `infra/CONFIGURATION.md` for complete reference.

Key variables:
- PostgreSQL: `POSTGRES_*`
- Kafka: `KAFKA_*`
- Producer: `PRODUCER_*`
- Backend: `POSTGRES_*`, `REDIS_URL`, `CORS_ORIGINS`
- Frontend: `VITE_API_URL`, `VITE_WS_URL`
- Streaming: `CHAT_WINDOW_*`, `ANOMALY_DETECTION_THRESHOLD`

---

## Troubleshooting by Service

### Zookeeper issues
```bash
docker compose logs zookeeper | grep -i error
docker compose exec zookeeper nc -z localhost 2181
```

### Kafka issues
```bash
docker compose logs kafka | grep -i error
docker compose exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092
```

### PostgreSQL issues
```bash
docker compose logs postgres | grep -i error
docker compose exec postgres pg_isready -U telemetra
```

### Backend connection issues
```bash
docker compose logs backend | grep -i "postgres\|redis\|kafka"
curl http://localhost:8000/health
```

### Data not flowing
```bash
docker compose logs spark-streaming-job | grep -i "aggregate\|written"
docker compose exec postgres psql -U telemetra -d telemetra -c "SELECT COUNT(*) FROM chat_summary_minute;"
```

---

## Additional Resources

- Main guide: `infra/README.md`
- Configuration: `infra/CONFIGURATION.md`
- Quick start: `QUICKSTART.md`
- Deployment: `DEPLOYMENT_CHECKLIST.md`
