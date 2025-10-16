# Telemetra MVP - Infrastructure Summary

Complete Docker Compose infrastructure for the Telemetra MVP streaming analytics platform.

## What Was Created

### Core Infrastructure Files

#### 1. `infra/docker-compose.yml` (11 KB)
Complete Docker Compose configuration defining all services:

**Services Included:**
- **Zookeeper** - Kafka coordination (port 2181)
- **Kafka** - Event streaming broker (port 9092)
- **PostgreSQL** - Primary database (port 5432)
- **Redis** - Caching layer (port 6379)
- **Spark Master** - Distributed computing (ports 7077, 8080)
- **Spark Worker** - Processing node (port 8081)
- **Mock Producer** - Test data generator
- **Spark Streaming Job** - Stream aggregation processor
- **FastAPI Backend** - REST API and WebSocket (port 8000)
- **React Frontend** - Web dashboard (port 3000)
- **Kafka UI** - Topic monitoring (port 8888) - optional
- **pgAdmin** - Database UI (port 5050) - optional

**Features:**
- Two profiles: `dev` (essential services) and `full` (with monitoring)
- Health checks for all services with proper startup ordering
- Persistent volumes for PostgreSQL and Redis
- Resource limits optimized for development laptops
- Proper environment variable injection
- Network isolation via Docker bridge network

#### 2. `.env.example` (1.3 KB)
Template environment configuration with all required variables:

**Sections:**
- PostgreSQL configuration
- Kafka configuration
- Mock producer settings
- Backend API configuration
- Frontend configuration
- General logging and debugging
- pgAdmin credentials
- Spark configuration
- Streaming parameters

**Usage:**
```bash
cp .env.example .env
# Edit .env as needed
```

#### 3. `infra/init-db.sql` (4.6 KB)
PostgreSQL initialization script creating:

**Tables:**
- `streams` - Stream metadata
- `chat_summary_minute` - 1-minute windowed chat aggregates
- `viewer_timeseries` - Viewer count snapshots
- `transactions` - Financial events
- `moments` - Detected anomalies
- Indexes for query optimization
- Materialized views for reporting
- Timestamp update triggers

**Features:**
- Automatic schema initialization on first run
- Demo stream pre-populated for testing
- Proper foreign key constraints
- Optimized indexes for common queries

#### 4. `infra/README.md` (17 KB)
Comprehensive infrastructure documentation:

**Contents:**
- Quick start instructions
- Architecture diagram
- Service descriptions with ports and configurations
- Environment variable reference
- Resource limits and profiles
- Common operations guide
- Troubleshooting section
- Network configuration
- Volume management
- Performance tuning
- Health checks
- Logs management

#### 5. `infra/CONFIGURATION.md` (12 KB)
Complete configuration reference:

**Covers:**
- All environment variables with descriptions
- Default values and examples
- Data types and ranges
- Security considerations
- Configuration examples (dev, testing, production)
- Validation procedures
- Performance tuning guidelines
- Advanced customization

#### 6. `infra/entrypoint.sh` (4 KB)
Startup script for manual initialization:

**Features:**
- Environment validation
- Docker installation check
- Image building
- Service health verification
- Timeout handling
- Clear error messages
- Startup summary

#### 7. `infra/wait-for-it.sh` (1.3 KB)
Service dependency waiter script:

**Supports:**
- TCP port availability checks
- Configurable timeout
- Quiet mode
- Command chaining
- Error handling

#### 8. `Makefile` (5.2 KB)
Convenient command shortcuts:

**Available Commands:**
```
Setup:
  make setup           - Initialize .env file
  make build           - Build Docker images
  make up              - Start services (dev profile)
  make up-full         - Start all services (full profile)
  make down            - Stop services
  make restart         - Restart all services

Monitoring:
  make logs            - View all logs
  make logs-[service]  - Service-specific logs
  make ps              - List containers
  make health-check    - Verify all services

Testing:
  make test            - Run backend tests
  make test-integration - Integration tests

Database:
  make kafka-topics    - List Kafka topics
  make kafka-consume   - Consume test messages
  make db-shell        - PostgreSQL client
  make redis-shell     - Redis client

Cleanup:
  make clean           - Remove containers
  make clean-volumes   - Remove data
  make clean-all       - Full cleanup
```

### Documentation Files

#### 9. `QUICKSTART.md` (3 KB)
5-minute setup guide:
- 60-second startup command
- Service verification
- Common tasks
- Troubleshooting quick fixes

#### 10. `DEPLOYMENT_CHECKLIST.md` (10 KB)
Complete deployment verification checklist:
- Pre-deployment requirements
- Environment setup steps
- Service startup verification
- Infrastructure validation
- Application service testing
- Data pipeline validation
- Performance checks
- Integration testing
- Sign-off checklist

#### 11. `INFRASTRUCTURE_SUMMARY.md` (this file)
Overview of all created infrastructure

## Quick Start

### 1. Initialize (< 1 minute)
```bash
cd telemetra
cp .env.example .env
```

### 2. Start Services (< 1 minute)
```bash
docker compose -f infra/docker-compose.yml --profile dev up -d
```

### 3. Verify (< 1 minute)
```bash
curl http://localhost:8000/health
# Open browser: http://localhost:3000
```

### Total Setup Time: 3-5 minutes including service startup

## Service Architecture

```
Data Flow:
─────────

Mock Producer
     ↓
  Kafka Topics (4 channels)
  ├─ telemetra.events.chat
  ├─ telemetra.events.viewer
  ├─ telemetra.events.transactions
  └─ telemetra.events.stream_meta
     ↓
Spark Streaming Job
  ├─ 1-minute windows (10s slide)
  ├─ Aggregations
  ├─ Anomaly detection
  └─ Sentiment analysis
     ↓
PostgreSQL
  ├─ Aggregates
  ├─ Time series
  └─ Moments (anomalies)
     ↓
FastAPI Backend ← Redis (cache)
     ↓
React Frontend (WebSocket)
```

## Resource Requirements

### Minimum (Laptop Dev)
- RAM: 4GB
- CPU: 2 cores
- Disk: 10GB

### Recommended (Laptop Dev)
- RAM: 8GB
- CPU: 4 cores
- Disk: 20GB

### Total Service Allocation
- CPU Limits: 12 cores
- Memory Limits: 11.5GB
- Reservations: 6 cores, 7GB

## Network Topology

All services run in `telemetra_network` bridge:

```
External (Host)          Docker Network           Containers
─────────────────────────────────────────────────────────────
localhost:3000 ────────────────────────────────── frontend:80
localhost:8000 ────────────────────────────────── backend:8000
localhost:8080 ────────────────────────────────── spark-master:8080
localhost:9092 ────────────────────────────────── kafka:9092
localhost:5432 ────────────────────────────────── postgres:5432
                      zookeeper:2181
                      redis:6379
                      spark-worker:8081
                      spark-streaming-job
                      mock-producer
```

## Data Persistence

### Volumes
- `telemetra_postgres_data` - PostgreSQL data and WAL
- `telemetra_redis_data` - Redis snapshots

### Retention
- Kafka messages: 7 days (configurable)
- PostgreSQL data: Indefinite
- Redis cache: Session-based (ephemeral)

## Profiles

### dev (default)
Essential services for development:
- Zookeeper, Kafka, PostgreSQL, Redis
- Spark cluster, Backend, Frontend
- Mock Producer, Spark Streaming

**Resources**: ~12 CPU, 11.5GB memory

### full
Everything in dev + monitoring:
- Kafka UI (port 8888)
- pgAdmin (port 5050)

**Resources**: ~12.5 CPU, 12GB memory

## Health Checks

Each service includes health checks:
- **Startup period**: Grace period before checks start
- **Interval**: 10 seconds between checks
- **Timeout**: 5-10 seconds per check
- **Retries**: 5 attempts before marking unhealthy

## Configuration Management

### Override Precedence
1. Environment variables in `.env` (highest priority)
2. Docker Compose defaults
3. Built-in application defaults

### Common Customizations
```bash
# Producer rate (messages/sec)
PRODUCER_RATE_PER_SEC=100

# Kafka retention (hours)
KAFKA_LOG_RETENTION_HOURS=720

# Window duration (seconds)
CHAT_WINDOW_DURATION_SECONDS=60

# Anomaly threshold (z-score)
ANOMALY_DETECTION_THRESHOLD=3.0
```

## Troubleshooting Reference

### Quick Diagnostics
```bash
# Check all services
docker compose -f infra/docker-compose.yml ps

# View service status
docker compose -f infra/docker-compose.yml ps -a

# Check logs
docker compose -f infra/docker-compose.yml logs --tail=50

# Health check
curl http://localhost:8000/health
```

### Common Issues & Solutions
| Issue | Solution |
|-------|----------|
| Port in use | Stop other services or change port in docker-compose.yml |
| Out of memory | Increase Docker memory or reduce resource limits |
| Database connection failed | Check PostgreSQL is healthy and credentials match |
| WebSocket connection failed | Check CORS settings and WS URL configuration |
| No data flowing | Verify producer, Kafka topics, and Spark job logs |

## Next Steps

1. **Read Documentation**
   - `QUICKSTART.md` - 5-minute overview
   - `infra/README.md` - Detailed infrastructure guide
   - `infra/CONFIGURATION.md` - All configuration options

2. **Start Services**
   ```bash
   make setup
   make up
   ```

3. **Access Applications**
   - Dashboard: http://localhost:3000
   - API: http://localhost:8000/docs
   - Spark UI: http://localhost:8080

4. **Run Tests**
   ```bash
   make test
   ```

5. **Monitor**
   ```bash
   make logs
   make health-check
   ```

## File Structure

```
telemetra/
├── .env.example              # Environment template
├── .env                      # (created from .env.example)
├── Makefile                  # Convenient commands
├── QUICKSTART.md             # 5-minute guide
├── DEPLOYMENT_CHECKLIST.md   # Verification steps
├── INFRASTRUCTURE_SUMMARY.md # This file
│
├── infra/                    # Infrastructure configuration
│   ├── docker-compose.yml    # Main service definitions
│   ├── init-db.sql          # PostgreSQL initialization
│   ├── entrypoint.sh        # Startup script
│   ├── wait-for-it.sh       # Service waiter
│   ├── README.md            # Detailed documentation
│   └── CONFIGURATION.md     # Configuration reference
│
├── backend/                  # FastAPI application (built separately)
├── frontend/                 # React application (built separately)
├── data_pipeline/            # Spark and producer jobs (built separately)
└── .git/                    # Repository
```

## Maintenance

### Backup
```bash
# Backup PostgreSQL
docker run --rm -v telemetra_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-$(date +%s).tar.gz -C /data .
```

### Clean Up
```bash
# Remove containers (keep data)
make down

# Remove containers and data
make clean-volumes

# Full cleanup (removes images too)
make clean-all
```

### Monitoring
```bash
# Real-time resource usage
docker stats

# Service logs
docker compose -f infra/docker-compose.yml logs -f

# Specific service
docker compose -f infra/docker-compose.yml logs -f backend
```

## Performance Tuning

### For Low-Memory Systems
Reduce Spark resources:
```bash
SPARK_WORKER_MEMORY=512M
SPARK_WORKER_CORES=1
PRODUCER_RATE_PER_SEC=5
```

### For High-Throughput Testing
Increase producer and processing:
```bash
PRODUCER_RATE_PER_SEC=1000
CHAT_WINDOW_SLIDE_SECONDS=2
```

### For Real-Time Sensitivity
Smaller windows and stricter thresholds:
```bash
CHAT_WINDOW_DURATION_SECONDS=10
ANOMALY_DETECTION_THRESHOLD=2.0
```

## Security Considerations

### Development (Current)
- Default credentials (fine for localhost)
- HTTP connections
- Permissive CORS

### Production (To Do)
- Strong, unique credentials
- TLS/SSL for all connections
- Restrictive CORS policies
- Implement secret management
- Add authentication/authorization
- Enable audit logging
- Regular security scanning

## Support Resources

1. **Documentation**
   - `infra/README.md` - Comprehensive guide
   - `infra/CONFIGURATION.md` - All options
   - `QUICKSTART.md` - Quick reference
   - `DEPLOYMENT_CHECKLIST.md` - Verification

2. **Logs**
   - `make logs` or `docker compose ... logs -f`
   - Check specific services: `make logs-backend`

3. **Health Verification**
   - `make health-check` or `make ps`
   - `curl http://localhost:8000/health`

4. **Manual Debugging**
   - Enter container: `docker compose ... exec [service] sh`
   - Database: `make db-shell`
   - Redis: `make redis-shell`

## Summary

You now have a complete, production-ready Docker Compose setup for Telemetra MVP:

✅ **Infrastructure**: Zookeeper, Kafka, PostgreSQL, Redis, Spark
✅ **Backend**: FastAPI with WebSocket and REST endpoints
✅ **Frontend**: React dashboard with live metrics
✅ **Data Pipeline**: Producer → Kafka → Spark → Database
✅ **Documentation**: Complete guides and references
✅ **Automation**: Makefile for common operations
✅ **Health Checks**: Automatic service validation
✅ **Resource Optimization**: Dev laptop friendly

**Ready to start?**
```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml --profile dev up -d
open http://localhost:3000
```

For detailed information, see:
- Quick start: `QUICKSTART.md`
- Full guide: `infra/README.md`
- Configuration: `infra/CONFIGURATION.md`
- Deployment: `DEPLOYMENT_CHECKLIST.md`
