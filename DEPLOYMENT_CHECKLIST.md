# Telemetra MVP - Deployment Checklist

Complete checklist for deploying and validating the Telemetra MVP infrastructure.

## Pre-Deployment

- [ ] Docker Desktop installed (20.10+)
- [ ] Docker Compose installed (1.29+)
- [ ] Minimum 8GB RAM available
- [ ] 20GB disk space free
- [ ] Git repository cloned/extracted

## Environment Setup

```bash
# Step 1: Navigate to project directory
cd telemetra

# Step 2: Create environment file
cp .env.example .env

# Step 3: Verify .env file
cat .env | head -20
```

- [ ] `.env` file created from `.env.example`
- [ ] `.env` file permissions are readable
- [ ] All required variables are present

## Docker Image Building

```bash
# Build all Docker images
docker compose -f infra/docker-compose.yml build --no-cache
```

- [ ] Zookeeper image built successfully
- [ ] Kafka image built successfully
- [ ] PostgreSQL image built successfully
- [ ] Redis image built successfully
- [ ] Spark images built successfully
- [ ] Backend image built successfully
- [ ] Frontend image built successfully
- [ ] Mock Producer image built successfully
- [ ] No build errors or warnings

## Service Startup (Dev Profile)

```bash
# Start all services with dev profile
docker compose -f infra/docker-compose.yml --profile dev up -d

# Verify containers are running
docker compose -f infra/docker-compose.yml ps
```

- [ ] All containers created successfully
- [ ] No container startup errors
- [ ] All containers have "Up" status (after 30s)

### Service Health Verification

```bash
# Check service health status
docker compose -f infra/docker-compose.yml ps --all

# View health details
docker compose -f infra/docker-compose.yml exec zookeeper nc -z localhost 2181
docker compose -f infra/docker-compose.yml exec kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```

- [ ] Zookeeper health: healthy/running
- [ ] Kafka health: healthy/running
- [ ] PostgreSQL health: healthy/running
- [ ] Redis health: healthy/running
- [ ] Spark Master health: healthy/running
- [ ] Spark Worker health: healthy/running

## Infrastructure Validation

### Kafka Setup

```bash
# List Kafka topics
docker compose -f infra/docker-compose.yml exec kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092

# Expected output:
# telemetra.events.chat
# telemetra.events.viewer
# telemetra.events.transactions
# telemetra.events.stream_meta
```

- [ ] Kafka broker is accessible
- [ ] Topics auto-created (4 expected)
- [ ] Topics can be listed successfully

### PostgreSQL Setup

```bash
# Connect to database and verify tables
docker compose -f infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra -c "\dt"

# Expected tables:
# - streams
# - chat_summary_minute
# - viewer_timeseries
# - transactions
# - moments
```

- [ ] PostgreSQL is accessible
- [ ] Database "telemetra" exists
- [ ] All required tables created
- [ ] Indexes created successfully
- [ ] Materialized views created

```bash
# Verify demo stream was created
docker compose -f infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra -c "SELECT * FROM streams;"

# Should return:
# id | stream_id    | name        | description
# 1  | demo_stream  | Demo Stream | Demo stream for testing Telemetra MVP
```

- [ ] Demo stream record exists

### Redis Setup

```bash
# Test Redis connectivity
docker compose -f infra/docker-compose.yml exec redis redis-cli ping

# Should output: PONG
```

- [ ] Redis is accessible
- [ ] Redis responds to PING

## Application Services Validation

### Backend API

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status":"ok"} or similar
```

- [ ] Backend is accessible on port 8000
- [ ] Health check returns success
- [ ] API returns correct status

```bash
# Check API documentation
curl http://localhost:8000/docs
```

- [ ] Swagger UI is accessible
- [ ] All routes are documented
- [ ] Schema validation working

```bash
# Test initial endpoints
curl http://localhost:8000/streams

# Should return streams array (initially empty or with demo_stream)
```

- [ ] REST endpoints respond correctly
- [ ] Response format is valid JSON

### WebSocket Connection

```bash
# Test WebSocket connectivity (using wscat or similar)
npm install -g wscat
wscat -c ws://localhost:8000/live/demo_stream

# Should connect and return: {"type":"connected"}
# Type: quit to exit
```

- [ ] WebSocket server is accessible
- [ ] WebSocket connections accepted
- [ ] Proper message format

Or use a simple curl test:
```bash
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/live/demo_stream
```

### Frontend Application

```bash
# Check frontend accessibility
curl -s http://localhost:3000 | head -20

# Should return HTML content with React app
```

- [ ] Frontend is accessible on port 3000
- [ ] HTML content returned
- [ ] React app loads in browser

```bash
# Verify in browser: http://localhost:3000
# Expected to see:
# - Dashboard loading
# - Live metrics widgets
# - WebSocket connection status
# - Real-time data updates
```

- [ ] Dashboard renders without errors
- [ ] Components visible and interactive
- [ ] WebSocket connection indicator shows connected
- [ ] Data updates visible (if producer running)

## Data Pipeline Validation

### Mock Producer

```bash
# Check producer logs
docker compose -f infra/docker-compose.yml logs --tail=50 mock-producer

# Should show messages being produced
```

- [ ] Producer container is running
- [ ] Messages are being produced
- [ ] No connection errors in logs
- [ ] Production rate matches PRODUCER_RATE_PER_SEC

```bash
# Consume messages from Kafka to verify
docker compose -f infra/docker-compose.yml exec kafka \
  kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --from-beginning \
  --max-messages 5

# Should display JSON messages from chat topic
```

- [ ] Messages present in chat topic
- [ ] Messages are valid JSON
- [ ] Message format includes required fields

### Spark Streaming Job

```bash
# Check Spark streaming job logs
docker compose -f infra/docker-compose.yml logs --tail=100 spark-streaming-job

# Look for:
# - No connection errors
# - Window processing logs
# - Database writes successful
```

- [ ] Spark job is running
- [ ] Connected to Kafka successfully
- [ ] Connected to PostgreSQL successfully
- [ ] Processing messages from Kafka
- [ ] Writing results to database

```bash
# Verify data in database
docker compose -f infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra -c \
  "SELECT COUNT(*) as aggregate_count FROM chat_summary_minute;"

# Should return count > 0 if streaming for a few minutes
```

- [ ] Aggregates being written to database
- [ ] Row count increasing over time
- [ ] Data persists across queries

## Performance & Resource Check

```bash
# Monitor resource usage
docker stats --no-stream

# Typical resource usage (dev profile):
# - Zookeeper: 20-50MB
# - Kafka: 200-300MB
# - PostgreSQL: 100-200MB
# - Redis: 10-20MB
# - Spark Master: 500MB-1GB
# - Spark Worker: 1-2GB
# - Backend: 100-200MB
# - Frontend: 50-100MB
```

- [ ] Total memory usage under 12GB
- [ ] CPU usage below 70% (idle)
- [ ] No OOM (Out of Memory) errors
- [ ] No container restarts

## Logs Inspection

```bash
# Check all logs for errors
docker compose -f infra/docker-compose.yml logs --tail=20 2>&1 | grep -i error

# Should return minimal or no errors
```

- [ ] No critical errors in logs
- [ ] No connection timeouts
- [ ] No authentication failures
- [ ] No data loss warnings

## Integration Testing

```bash
# Test full flow: Data -> Kafka -> Spark -> Database -> API -> Frontend

# 1. Verify data flowing through pipeline
docker compose -f infra/docker-compose.yml logs --tail=5 mock-producer | grep -i "message\|produced"

# 2. Verify Spark processing
docker compose -f infra/docker-compose.yml logs --tail=5 spark-streaming-job | grep -i "window\|aggregate"

# 3. Verify API serving data
curl -s http://localhost:8000/streams | jq .

# 4. Open browser and verify dashboard updates
# http://localhost:3000
```

- [ ] Producer sending messages to Kafka
- [ ] Spark receiving and processing messages
- [ ] Database receiving aggregates
- [ ] API returning data correctly
- [ ] Frontend updating with live data

## Cleanup & Shutdown

```bash
# Stop services gracefully
docker compose -f infra/docker-compose.yml down

# Verify containers stopped
docker compose -f infra/docker-compose.yml ps

# Should show no running containers
```

- [ ] All containers stopped successfully
- [ ] No containers in "Exited" state with errors
- [ ] No orphaned containers

## Backup

```bash
# Backup PostgreSQL volume
docker run --rm -v telemetra_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# Backup Redis volume
docker run --rm -v telemetra_redis_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/redis-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .
```

- [ ] Database backup created
- [ ] Cache backup created
- [ ] Backups stored safely

## Troubleshooting Guide

If any checks failed:

### Service fails to start
1. Check Docker is running: `docker ps`
2. Review service logs: `docker compose -f infra/docker-compose.yml logs [service]`
3. Check port conflicts: Windows `netstat -ano | findstr :PORT`
4. Increase Docker memory and restart

### Backend health check fails
1. Check PostgreSQL connection: `docker compose -f infra/docker-compose.yml logs backend | tail -50`
2. Verify .env variables
3. Check database initialization: `docker compose -f infra/docker-compose.yml exec postgres psql -U telemetra -d telemetra -c "\dt"`
4. Restart backend: `docker compose -f infra/docker-compose.yml restart backend`

### WebSocket connection fails
1. Check backend logs for connection errors
2. Verify VITE_WS_URL in .env
3. Check browser console for CORS errors
4. Verify backend is running and healthy

### Data not flowing through pipeline
1. Check producer: `docker compose -f infra/docker-compose.yml logs mock-producer`
2. Check Kafka topics exist: `docker compose -f infra/docker-compose.yml exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092`
3. Check Spark job: `docker compose -f infra/docker-compose.yml logs spark-streaming-job`
4. Verify PostgreSQL: `docker compose -f infra/docker-compose.yml exec postgres psql -U telemetra -d telemetra -c "SELECT COUNT(*) FROM chat_summary_minute;"`

### Performance issues
1. Check resource limits: `docker stats`
2. Increase Docker allocated resources
3. Reduce PRODUCER_RATE_PER_SEC if needed
4. Check for slow queries in PostgreSQL logs

## Sign-Off

- [ ] All infrastructure services running
- [ ] All health checks passing
- [ ] Data pipeline functional
- [ ] Frontend dashboard displaying data
- [ ] No critical errors in logs
- [ ] Ready for development/testing

## Next Steps

1. **Develop**: Start building features and running tests
2. **Scale**: Increase producer rate, add load testing
3. **Monitor**: Set up Prometheus/Grafana for metrics
4. **Deploy**: Prepare for staging/production deployment

## Quick Reference

### Essential Commands
```bash
# Startup
cp .env.example .env
docker compose -f infra/docker-compose.yml --profile dev up -d

# Monitoring
docker compose -f infra/docker-compose.yml logs -f
docker compose -f infra/docker-compose.yml ps

# Health
curl http://localhost:8000/health
http://localhost:3000

# Shutdown
docker compose -f infra/docker-compose.yml down
```

### Service Ports
- Frontend: 3000
- Backend API: 8000
- Spark UI: 8080
- Kafka UI: 8888
- pgAdmin: 5050
- PostgreSQL: 5432
- Redis: 6379
- Kafka: 9092
- Zookeeper: 2181

### Default Credentials
- PostgreSQL: telemetra / telemetra_dev_password
- pgAdmin: admin@telemetra.local / admin
