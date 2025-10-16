# Telemetra MVP - Infrastructure Setup

Complete Docker Compose configuration for the Telemetra MVP streaming analytics platform.

## Quick Start

### Prerequisites
- Docker Desktop (20.10+)
- Docker Compose (1.29+)
- 8GB available RAM (4GB minimum)
- 20GB disk space for volumes

### One-Command Setup

```bash
# Clone/extract the repository and navigate to it
cd telemetra

# Copy environment configuration
cp .env.example .env

# Start all services
docker compose -f infra/docker-compose.yml --profile dev up -d

# Wait for services to be ready (typically 30-60 seconds)
docker compose -f infra/docker-compose.yml ps

# Access the dashboard
open http://localhost:3000
```

After starting, you should see:
- Frontend dashboard at http://localhost:3000
- API swagger docs at http://localhost:8000/docs
- Health check: `curl http://localhost:8000/health`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Telemetra MVP Architecture                                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Mock Producer (Python)                              │   │
│  │ Generates: chat, viewers, transactions, stream_meta │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Kafka Cluster (Zookeeper + Broker)                 │   │
│  │ Topics: telemetra.events.*                          │   │
│  └─────────────────────────────────────────────────────┘   │
│        ↙         ↓         ↘         ↙                      │
│   ┌────────┐  ┌────────────────┐  ┌──────────┐             │
│   │ Spark  │  │ Spark Streaming│  │  Redis   │             │
│   │ Master │  │ Job            │  │ (Cache)  │             │
│   └────────┘  └────────┬───────┘  └──────────┘             │
│        ↓                ↓                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ PostgreSQL (Primary Database)                       │   │
│  │ Tables: streams, chat_summary_minute,               │   │
│  │         viewer_timeseries, transactions, moments    │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↑                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ FastAPI Backend                                      │   │
│  │ Routes: /health, /streams, /live/{stream_id}        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           ↓                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ React Frontend (TypeScript + Vite)                  │   │
│  │ Dashboard: PulseBar, ChatFlow, EmoteCloud           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Services

### Core Infrastructure

#### Zookeeper (2181)
- Coordination service for Kafka broker
- Single node configuration
- Health check: TCP 2181

#### Kafka (9092)
- Message broker for event streaming
- Auto-creates topics: `telemetra.events.*`
- PLAINTEXT connections on port 9092
- Retention: 7 days (configurable via `KAFKA_LOG_RETENTION_HOURS`)

**Key Topics:**
- `telemetra.events.chat` - Chat messages and metadata
- `telemetra.events.viewer` - Viewer count snapshots
- `telemetra.events.transactions` - Purchase/subscription events
- `telemetra.events.stream_meta` - Stream metadata updates

#### PostgreSQL (5432)
- Primary database for aggregates and analytics
- Volumes: `telemetra_postgres_data` (persistent)
- Auto-initialization with `infra/init-db.sql`
- Default credentials: `telemetra:telemetra_dev_password`

**Schemas:**
- `streams` - Stream metadata
- `chat_summary_minute` - 1-minute windowed chat aggregates
- `viewer_timeseries` - Viewer count time series
- `transactions` - Financial events
- `moments` - Detected anomalies and interesting events

#### Redis (6379)
- In-memory cache for real-time metrics
- Persistence: `telemetra_redis_data` volume
- Used by backend for latest metrics cache
- Connection: `redis://redis:6379`

#### Spark Master (7077, 8080)
- Master node for distributed processing
- Web UI on port 8080
- RPC on port 7077
- Receives jobs from spark-submit or scheduling services

#### Spark Worker (8081)
- Worker node for distributed computation
- Allocated: 2 CPU cores, 1GB memory

### Processing Services

#### Mock Producer (Python)
- Generates synthetic stream events
- Target Kafka topics: chat, viewers, transactions, stream_meta
- Configurable rate: `PRODUCER_RATE_PER_SEC` (default: 10 msg/sec)
- Configurable streams: `PRODUCER_CHANNELS` (default: demo_stream)

#### Spark Streaming Job (Python/PySpark)
- Reads events from Kafka topics
- Performs 1-minute windowed aggregations with 10-second slides
- Computes: chat counts, unique chatters, top emotes
- Anomaly detection: Z-score on chat rate
- Sentiment analysis: lexicon-based fallback
- Writes results to PostgreSQL via JDBC

### Application Services

#### Backend API (FastAPI, 8000)
- REST API for stream data queries
- WebSocket `/live/{stream_id}` for real-time metrics
- Health check: `GET /health`
- Endpoints:
  - `GET /streams` - List all streams
  - `GET /streams/{id}/metrics` - Get aggregated metrics
  - `GET /streams/{id}/moments` - Get detected moments
  - `WS /live/{stream_id}` - Real-time metric stream

#### Frontend (React + Vite, 3000)
- Real-time dashboard
- Components:
  - PulseBar: Animated viewer count
  - ChatFlow: Chat rate visualization
  - EmoteCloud: Top emotes bubble chart
  - MomentsTimeline: Detected anomalies
- Auto-connects to backend WebSocket

### Optional Services

#### Kafka UI (8888)
- Web interface for Kafka monitoring
- View topics, messages, consumer groups
- Only included in `full` profile

#### pgAdmin (5050)
- PostgreSQL management UI
- Default: admin@telemetra.local / admin
- Only included in `full` profile

## Configuration

### Environment Variables

All configuration is managed via `.env` file. Key variables:

```bash
# Database
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=telemetra_dev_password
POSTGRES_DB=telemetra

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_LOG_RETENTION_HOURS=168
PRODUCER_RATE_PER_SEC=10
PRODUCER_CHANNELS=demo_stream

# Backend
REDIS_URL=redis://redis:6379
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DEBUG=false

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Logging
LOG_LEVEL=INFO
```

### Resource Limits

Each service has development-appropriate resource limits:

| Service | CPU Limit | Memory Limit | CPU Reserve | Memory Reserve |
|---------|-----------|--------------|-------------|----------------|
| Zookeeper | 0.5 | 512M | 0.25 | 256M |
| Kafka | 1.0 | 1G | 0.5 | 512M |
| PostgreSQL | 1.0 | 1G | 0.5 | 512M |
| Redis | 0.5 | 512M | 0.25 | 256M |
| Spark Master | 1.0 | 1.5G | 0.5 | 1G |
| Spark Worker | 2.0 | 2G | 1.0 | 1.5G |
| Backend | 1.0 | 1G | 0.5 | 512M |
| Frontend | 0.5 | 512M | 0.25 | 256M |
| Mock Producer | 0.5 | 512M | 0.25 | 256M |
| Spark Streaming | 2.0 | 2G | 1.0 | 1.5G |

**Total: ~12 CPU, 11.5GB memory** (in dev profile)

### Profiles

#### dev (default)
Minimal setup for development:
- Zookeeper, Kafka, PostgreSQL, Redis
- Spark Master & Worker
- Backend, Frontend
- Mock Producer, Spark Streaming Job
- **Total: ~12 CPU, 11.5GB memory**

```bash
docker compose -f infra/docker-compose.yml --profile dev up -d
```

#### full
Complete setup with monitoring:
- Everything in dev profile +
- Kafka UI (Kafka monitoring)
- pgAdmin (PostgreSQL UI)
- **Total: ~12.5 CPU, 12GB memory**

```bash
docker compose -f infra/docker-compose.yml --profile full up -d
```

## Common Operations

### Using Make

```bash
# Setup (first time)
make setup

# Start services
make up                  # dev profile (default)
make up-full             # includes pgAdmin and Kafka UI

# Monitoring
make logs                # all services
make logs-backend        # specific service
make ps                  # list containers
make health-check        # verify all services

# Testing
make test                # run backend unit tests
make test-integration    # run integration tests

# Utilities
make kafka-topics        # list Kafka topics
make kafka-consume       # consume chat messages
make db-shell            # PostgreSQL client
make redis-shell         # Redis client

# Cleanup
make down                # stop services
make clean               # remove containers
make clean-volumes       # remove data (WARNING: data loss!)
make clean-all           # full cleanup
```

### Manual Docker Compose

```bash
# View logs
docker compose -f infra/docker-compose.yml logs -f backend
docker compose -f infra/docker-compose.yml logs -f spark-streaming-job

# Check service status
docker compose -f infra/docker-compose.yml ps

# Execute commands in containers
docker compose -f infra/docker-compose.yml exec backend pytest
docker compose -f infra/docker-compose.yml exec postgres psql -U telemetra -d telemetra

# Restart specific service
docker compose -f infra/docker-compose.yml restart backend
```

## Troubleshooting

### Services Not Starting

**Symptom:** Services fail to start or keep restarting

**Solution:**
1. Check logs: `make logs`
2. Verify resource availability: `docker stats`
3. Check port conflicts: `netstat -ano | findstr :8000` (Windows)
4. Clean up and restart:
   ```bash
   make clean-volumes
   make up
   ```

### Backend Cannot Connect to PostgreSQL

**Symptom:** Backend logs show connection refused

**Solution:**
1. Verify PostgreSQL is healthy: `docker compose -f infra/docker-compose.yml ps postgres`
2. Check connection string in logs
3. Verify credentials in `.env` match database initialization
4. Ensure PostgreSQL has completed initialization

### Kafka Topics Not Created

**Symptom:** Producer fails to send messages, "topic does not exist"

**Solution:**
1. Verify Kafka is running: `docker compose -f infra/docker-compose.yml ps kafka`
2. Create topics manually:
   ```bash
   docker compose -f infra/docker-compose.yml exec kafka \
     kafka-topics.sh --create \
     --bootstrap-server localhost:9092 \
     --topic telemetra.events.chat \
     --partitions 1 \
     --replication-factor 1
   ```
3. Check auto-creation is enabled in docker-compose.yml: `KAFKA_AUTO_CREATE_TOPICS_ENABLE=true`

### Frontend Cannot Connect to Backend

**Symptom:** Frontend shows "Failed to connect to WebSocket"

**Solution:**
1. Verify backend is healthy: `curl http://localhost:8000/health`
2. Check CORS settings in backend environment
3. Verify VITE_WS_URL is correct in `.env`
4. Check browser console for specific errors

### Out of Memory

**Symptom:** Docker containers killed or system becomes unresponsive

**Solution:**
1. Stop unnecessary services
2. Increase Docker Desktop memory allocation (Settings → Resources)
3. Reduce Spark memory: Update `SPARK_WORKER_MEMORY` in `.env`
4. Check for memory leaks: `docker stats`

### Database Initialization Failed

**Symptom:** PostgreSQL starts but tables don't exist

**Solution:**
1. Check if init script was executed:
   ```bash
   docker compose -f infra/docker-compose.yml exec postgres \
     psql -U telemetra -d telemetra -c "\dt"
   ```
2. Manually run init script:
   ```bash
   docker compose -f infra/docker-compose.yml exec postgres \
     psql -U telemetra -d telemetra -f /docker-entrypoint-initdb.d/01-init.sql
   ```
3. Reset and restart:
   ```bash
   make clean-volumes
   make up
   ```

## Network

All services communicate via the `telemetra_network` bridge network:

| Service | Internal Address | Port |
|---------|------------------|------|
| Zookeeper | zookeeper | 2181 |
| Kafka | kafka | 29092 (internal) / 9092 (host) |
| PostgreSQL | postgres | 5432 |
| Redis | redis | 6379 |
| Spark Master | spark-master | 7077 |
| Spark Worker | spark-worker | 7078 |
| Backend | backend | 8000 |
| Frontend | frontend | 80 |

## Volumes

Persistent data is stored in Docker volumes:

| Volume | Service | Purpose |
|--------|---------|---------|
| `telemetra_postgres_data` | PostgreSQL | Database files and WAL |
| `telemetra_redis_data` | Redis | Redis RDB snapshots |

To back up data:
```bash
docker run --rm -v telemetra_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz -C /data .
```

To restore:
```bash
docker run --rm -v telemetra_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /data
```

## Performance Tuning

### For Development (Default)
- Adequate for local testing and MVP
- Supports ~100 msg/sec through Kafka
- Single Spark worker node

### For Load Testing
1. Increase producer rate:
   ```bash
   PRODUCER_RATE_PER_SEC=100 make restart
   ```
2. Monitor resource usage:
   ```bash
   docker stats
   ```
3. Increase resource limits in docker-compose.yml if needed

### For Production
- Use dedicated Kafka cluster (Confluent Cloud or self-managed)
- Scale Spark cluster horizontally (multiple workers)
- Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- Use managed Redis (AWS ElastiCache, Google Memorystore)
- Add load balancer for backend
- Enable TLS/HTTPS for all connections
- Implement proper secret management (AWS Secrets Manager, HashiCorp Vault)

## Health Checks

Each service includes health check configuration:

```bash
# Manual health verification
curl http://localhost:8000/health
curl http://localhost:3000
docker compose -f infra/docker-compose.yml ps
```

Health check status in container output:
- `healthy` - Service is ready
- `starting` - Service is initializing
- `unhealthy` - Service has issues

## Logs

View logs for debugging:

```bash
# All services
docker compose -f infra/docker-compose.yml logs

# Specific service with tail
docker compose -f infra/docker-compose.yml logs -f backend

# Specific service, last 100 lines
docker compose -f infra/docker-compose.yml logs --tail=100 backend

# With timestamps
docker compose -f infra/docker-compose.yml logs --timestamps backend
```

## Next Steps

1. Start services: `make up`
2. Access dashboard: http://localhost:3000
3. View API docs: http://localhost:8000/docs
4. Monitor Kafka: http://localhost:8888
5. Run tests: `make test`
6. Check logs: `make logs`

## Support

For issues:
1. Check logs: `docker compose -f infra/docker-compose.yml logs`
2. Review troubleshooting section above
3. Check service health: `make health-check`
4. Reset everything: `make clean-all && make up`
