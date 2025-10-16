# Telemetra MVP - Quick Start Guide

Get the Telemetra MVP infrastructure running in 5 minutes.

## 60-Second Setup

```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Start all services
docker compose -f infra/docker-compose.yml --profile dev up -d

# 3. Access the dashboard
# Open browser to: http://localhost:3000

# Done! Services are starting...
```

That's it! Services will be ready in 30-60 seconds.

## What's Running

After the above commands:

- **Frontend Dashboard** at http://localhost:3000
  - Real-time metrics visualization
  - Live viewer count and chat rate
  - Detected moments/anomalies timeline

- **Backend API** at http://localhost:8000
  - REST endpoints for stream data
  - WebSocket for live metrics
  - Swagger docs at http://localhost:8000/docs

- **Kafka Broker** with auto-generated topics
  - Mock producer pushing test data
  - 4 topics: chat, viewer, transactions, stream_meta

- **PostgreSQL Database** for persistence
  - Aggregated metrics
  - Historical data
  - Detected anomalies

- **Spark Streaming** processing Kafka topics
  - 1-minute windowed aggregations
  - Anomaly detection
  - Data enrichment

- **Redis Cache** for latest metrics

## Verify Everything Works

```bash
# Check all services are running
docker compose -f infra/docker-compose.yml ps

# Expected output: All services in "Up" state

# Quick health check
curl http://localhost:8000/health

# Expected: {"status":"ok"}

# View live metrics in browser
# http://localhost:3000
```

## Common Tasks

### View Logs

```bash
# All services
docker compose -f infra/docker-compose.yml logs -f

# Specific service
docker compose -f infra/docker-compose.yml logs -f backend
docker compose -f infra/docker-compose.yml logs -f spark-streaming-job
docker compose -f infra/docker-compose.yml logs -f mock-producer
```

### Monitor Kafka

```bash
# View available topics
docker compose -f infra/docker-compose.yml exec kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092

# Consume chat messages
docker compose -f infra/docker-compose.yml exec kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --from-beginning \
  --max-messages 10
```

### Access Database

```bash
# PostgreSQL client
docker compose -f infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra

# Useful queries
SELECT * FROM streams;
SELECT COUNT(*) FROM chat_summary_minute;
SELECT * FROM moments ORDER BY timestamp DESC LIMIT 5;
```

### Stop Services

```bash
# Stop all services (keeps data)
docker compose -f infra/docker-compose.yml down

# Clean up everything (loses data)
docker compose -f infra/docker-compose.yml down -v
```

## Using Make (Optional)

If you have `make` installed, commands are simpler:

```bash
# Setup
make setup

# Start
make up

# View logs
make logs

# Specific service logs
make logs-backend
make logs-spark
make logs-producer

# Health check
make health-check

# Stop
make down

# See all commands
make help
```

## Adjusting Configuration

Edit `.env` to customize:

```bash
# Producer message rate (messages per second)
PRODUCER_RATE_PER_SEC=10

# Kafka message retention (hours)
KAFKA_LOG_RETENTION_HOURS=168

# Log level
LOG_LEVEL=INFO

# Database credentials
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=telemetra_dev_password
```

Then restart:
```bash
docker compose -f infra/docker-compose.yml restart
```

## Advanced: Full Profile with Monitoring

Start with all optional services (Kafka UI, pgAdmin):

```bash
docker compose -f infra/docker-compose.yml --profile full --profile dev up -d
```

Additional access points:
- **Kafka UI** at http://localhost:8888
- **pgAdmin** at http://localhost:5050
  - Email: admin@telemetra.local
  - Password: admin

## System Requirements

- **Memory**: 8GB recommended (minimum 4GB + swap)
- **CPU**: 4 cores recommended
- **Disk**: 20GB free space
- **Docker**: 20.10+
- **Docker Compose**: 1.29+

If services crash with OOM (Out of Memory):
1. Increase Docker Desktop memory allocation
2. Reduce `SPARK_WORKER_MEMORY` in `.env`
3. Lower `PRODUCER_RATE_PER_SEC`

## Troubleshooting

### "Port already in use"
```bash
# Find what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Mac/Linux

# Kill the process or use different port in docker-compose.yml
```

### "Cannot connect to backend"
```bash
# Check if service is running
docker compose -f infra/docker-compose.yml ps

# View logs
docker compose -f infra/docker-compose.yml logs backend

# Restart
docker compose -f infra/docker-compose.yml restart backend
```

### "Database connection failed"
```bash
# Check PostgreSQL is healthy
docker compose -f infra/docker-compose.yml ps postgres

# Check logs
docker compose -f infra/docker-compose.yml logs postgres

# Verify tables were created
docker compose -f infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra -c "\dt"
```

### "No data flowing through pipeline"
```bash
# Check producer
docker compose -f infra/docker-compose.yml logs mock-producer

# Verify Kafka has messages
docker compose -f infra/docker-compose.yml exec kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092

# Check Spark job
docker compose -f infra/docker-compose.yml logs spark-streaming-job
```

## Resource Usage

Typical resource usage:

```bash
# View current resource usage
docker stats

# Expected (all services running):
# Total: ~3GB RAM, 0.5-1.0 CPU (idle)
```

## Development Workflow

```bash
# 1. Start services
docker compose -f infra/docker-compose.yml --profile dev up -d

# 2. Make code changes in your IDE

# 3. Rebuild specific service
docker compose -f infra/docker-compose.yml build backend --no-cache

# 4. Restart service
docker compose -f infra/docker-compose.yml restart backend

# 5. View logs to verify
docker compose -f infra/docker-compose.yml logs -f backend

# 6. Stop when done
docker compose -f infra/docker-compose.yml down
```

## Testing Data Pipeline

```bash
# Generate 100 messages quickly
docker compose -f infra/docker-compose.yml exec mock-producer \
  python -c "from producer import produce_messages; produce_messages(rate=100, duration=1)"

# Monitor Spark processing
docker compose -f infra/docker-compose.yml logs -f spark-streaming-job

# Verify data in database
docker compose -f infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra -c "SELECT COUNT(*) FROM chat_summary_minute;"
```

## Network

All services communicate internally via Docker network:

| Service | Port | Internal URL |
|---------|------|-------------|
| Backend | 8000 | http://backend:8000 |
| PostgreSQL | 5432 | postgres://telemetra:password@postgres:5432/telemetra |
| Redis | 6379 | redis://redis:6379 |
| Kafka | 29092 | kafka:29092 |
| Spark Master | 7077 | spark://spark-master:7077 |

## Next Steps

1. **Dashboard**: Customize visualizations in `frontend/`
2. **API**: Add new endpoints in `backend/`
3. **Producer**: Add more realistic test data in `data_pipeline/producer/`
4. **Spark**: Enhance aggregations in `data_pipeline/spark/`
5. **Database**: Add materialized views for reporting

## Resources

- API Docs: http://localhost:8000/docs
- GitHub: [Repository]
- Issues: [Issue Tracker]
- Docs: See `infra/README.md` for detailed documentation

## Getting Help

```bash
# View all available make commands
make help

# View docker compose help
docker compose --help

# Check service logs
docker compose -f infra/docker-compose.yml logs [service-name]

# Full deployment checklist
cat DEPLOYMENT_CHECKLIST.md
```

---

**That's it!** You now have a fully functional Telemetra MVP running locally.
Open http://localhost:3000 and start exploring real-time streaming analytics.
