# Telemetra Backend - Quick Start Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Docker (optional, for containerized deployment)

## Installation & Setup

### Option 1: Local Development (without Docker)

1. **Navigate to backend directory**:
   ```bash
   cd backend/
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your database credentials:
   ```env
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=telemetra
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password

   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

5. **Start the server**:
   ```bash
   python -m backend.main
   # Or using uvicorn directly:
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Verify it's running**:
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"ok"}
   ```

7. **Access API documentation**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Option 2: Docker Deployment

1. **Build Docker image**:
   ```bash
   docker build -t telemetra-backend .
   ```

2. **Run container** (with environment variables):
   ```bash
   docker run -d \
     --name telemetra-backend \
     -p 8000:8000 \
     -e POSTGRES_HOST=postgres \
     -e POSTGRES_PORT=5432 \
     -e POSTGRES_DB=telemetra \
     -e POSTGRES_USER=telemetra_user \
     -e POSTGRES_PASSWORD=telemetra_pass \
     -e REDIS_HOST=redis \
     -e REDIS_PORT=6379 \
     telemetra-backend
   ```

3. **Or use Docker Compose** (from project root):
   ```bash
   docker compose -f infra/docker-compose.yml up backend
   ```

4. **Check logs**:
   ```bash
   docker logs -f telemetra-backend
   ```

### Option 3: Using Makefile

```bash
# Install dependencies
make install

# Run development server
make run

# Run tests
make test

# Build Docker image
make docker-build

# Run Docker container
make docker-run
```

## API Endpoints

### Health Check

```bash
# Simple health check
curl http://localhost:8000/health

# Detailed health check (includes database & Redis status)
curl http://localhost:8000/api/v1/health
```

### List Streams

```bash
# Get all active streams
curl http://localhost:8000/api/v1/streams

# With pagination
curl http://localhost:8000/api/v1/streams?limit=10&offset=0
```

### Get Stream Metrics

```bash
# Get metrics for a specific stream
curl http://localhost:8000/api/v1/streams/demo_stream/metrics

# With limit
curl http://localhost:8000/api/v1/streams/demo_stream/metrics?limit=20
```

### Get Stream Moments

```bash
# Get detected moments/anomalies
curl http://localhost:8000/api/v1/streams/demo_stream/moments

# With limit
curl http://localhost:8000/api/v1/streams/demo_stream/moments?limit=10
```

### WebSocket Live Stream

**JavaScript Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live/demo_stream');

ws.onopen = () => {
  console.log('Connected to live stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);

  if (data.type === 'connected') {
    console.log('Welcome message:', data.message);
  } else {
    // Metric update
    console.log('Viewer count:', data.viewer_count);
    console.log('Chat rate:', data.chat_rate);
    console.log('Recent moments:', data.recent_moments);
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

**Python Example**:
```python
import asyncio
import websockets
import json

async def connect_to_stream(stream_id):
    uri = f"ws://localhost:8000/ws/live/{stream_id}"

    async with websockets.connect(uri) as websocket:
        print(f"Connected to {stream_id}")

        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data}")

asyncio.run(connect_to_stream("demo_stream"))
```

**curl/wscat Example**:
```bash
# Install wscat if not already installed
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/live/demo_stream
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r tests/requirements.txt
```

### Run All Tests

```bash
# Basic test run
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=backend --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Specific Tests

```bash
# Run health endpoint tests only
pytest tests/test_health.py

# Run WebSocket tests only
pytest tests/test_websocket.py

# Run specific test function
pytest tests/test_health.py::TestHealthEndpoint::test_health_check_sync

# Run tests matching a pattern
pytest -k "websocket"
```

### Test with Docker

```bash
# Build and run tests in Docker
docker build -t telemetra-backend-test --target builder .
docker run --rm telemetra-backend-test pytest
```

## Troubleshooting

### Issue: Database connection fails

**Symptoms**:
```
Failed to initialize database pool
```

**Solution**:
1. Verify PostgreSQL is running:
   ```bash
   psql -h localhost -U telemetra_user -d telemetra
   ```

2. Check environment variables in `.env`
3. Ensure database exists:
   ```bash
   createdb telemetra
   ```

### Issue: Redis connection fails

**Symptoms**:
```
Failed to initialize Redis client
```

**Solution**:
1. Verify Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. Check Redis host and port in `.env`

### Issue: WebSocket not receiving data

**Symptoms**: Connected but no metric updates

**Possible Causes**:
1. No data in database tables
2. Stream ID doesn't exist
3. Database queries timing out

**Solution**:
1. Check if data exists:
   ```sql
   SELECT COUNT(*) FROM chat_summary_minute;
   SELECT COUNT(*) FROM viewer_timeseries;
   ```

2. Verify stream exists:
   ```sql
   SELECT * FROM streams WHERE stream_id = 'demo_stream';
   ```

3. Check application logs for errors

### Issue: Docker container won't start

**Solution**:
1. Check logs:
   ```bash
   docker logs telemetra-backend
   ```

2. Verify environment variables are set correctly

3. Ensure PostgreSQL and Redis containers are running:
   ```bash
   docker ps | grep -E "postgres|redis"
   ```

4. Check network connectivity:
   ```bash
   docker exec telemetra-backend ping postgres
   docker exec telemetra-backend ping redis
   ```

### Issue: Permission denied on entrypoint.sh

**Solution**:
```bash
chmod +x entrypoint.sh
# Rebuild Docker image
docker build -t telemetra-backend .
```

## Development Workflow

### 1. Make Code Changes

Edit files in `backend/`:
- `api/routes.py` - REST endpoints
- `api/websocket.py` - WebSocket handlers
- `db/database.py` - Database queries
- `models/schemas.py` - Pydantic models

### 2. Test Changes

```bash
# Run relevant tests
pytest tests/test_health.py -v

# Or run all tests
make test
```

### 3. Check Code Quality

```bash
# Format code
make format

# Lint code
make lint
```

### 4. Run Locally

```bash
# Start with auto-reload
make run

# Or manually
uvicorn backend.main:app --reload
```

### 5. Rebuild Docker Image

```bash
make docker-build
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_HOST` | Yes | localhost | PostgreSQL host |
| `POSTGRES_PORT` | Yes | 5432 | PostgreSQL port |
| `POSTGRES_DB` | Yes | telemetra | Database name |
| `POSTGRES_USER` | Yes | telemetra_user | Database user |
| `POSTGRES_PASSWORD` | Yes | - | Database password |
| `REDIS_HOST` | Yes | localhost | Redis host |
| `REDIS_PORT` | Yes | 6379 | Redis port |
| `REDIS_DB` | No | 0 | Redis database number |
| `REDIS_PASSWORD` | No | - | Redis password (if auth enabled) |
| `HOST` | No | 0.0.0.0 | Server bind address |
| `PORT` | No | 8000 | Server port |
| `DEBUG` | No | false | Debug mode |
| `LOG_LEVEL` | No | INFO | Logging level |
| `CACHE_TTL_METRICS` | No | 60 | Metrics cache TTL (seconds) |
| `WS_MESSAGE_INTERVAL` | No | 1.5 | WebSocket update interval (seconds) |
| `CORS_ORIGINS` | No | localhost:3000 | Allowed CORS origins |

## Next Steps

1. **Set up database schema**: Run migrations from the data pipeline
2. **Start data pipeline**: Ensure Kafka producer and Spark jobs are running
3. **Test WebSocket**: Connect and verify live data streaming
4. **Integrate with frontend**: Connect React dashboard to API
5. **Monitor performance**: Check logs and metrics

## Additional Resources

- Full API Documentation: http://localhost:8000/docs
- Backend README: [README.md](README.md)
- Project Documentation: [../README.md](../README.md)
- Telemetra Architecture: See project root for diagrams

## Support

For issues or questions:
1. Check application logs
2. Review database connectivity
3. Verify all dependencies are running
4. Consult troubleshooting section above
