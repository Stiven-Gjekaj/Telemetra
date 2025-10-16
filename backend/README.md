# Telemetra — Backend

[![CI](https://img.shields.io/github/actions/workflow/status/Stiven-Gjekaj/Telemetra/ci.yml?branch=main&label=CI)](https://github.com/Stiven-Gjekaj/Telemetra/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)

[← Back to main README](../README.md)

---

## Overview

The Telemetra backend is a [FastAPI](https://fastapi.tiangolo.com/) service that provides REST endpoints and WebSocket streaming for real-time streaming analytics. It consumes aggregated metrics from PostgreSQL, caches frequently accessed data in Redis, and exposes a clean API for the frontend dashboard.

**Key Responsibilities:**
- Serve REST API for streams, metrics, and detected moments
- Stream live metrics via WebSocket
- Query PostgreSQL for historical aggregates
- Cache latest metrics in Redis for sub-millisecond responses
- Provide health checks for all dependencies

---

## Architecture

```
┌──────────────┐
│  PostgreSQL  │──┐
│   (Metrics)  │  │
└──────────────┘  │
                  ▼
┌──────────────┐  ┌────────────┐
│    Redis     │─→│  FastAPI   │
│   (Cache)    │  │  Backend   │
└──────────────┘  └─────┬──────┘
                        │
                        ├─→ REST API (port 8000)
                        └─→ WebSocket (port 8000)
```

### Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** 0.109.0 — Async web framework with automatic OpenAPI docs
- **[asyncpg](https://github.com/MagicStack/asyncpg)** 0.29.0 — High-performance async PostgreSQL driver
- **[Redis](https://redis-py.readthedocs.io/)** 5.0.1 — Redis client for caching
- **[Pydantic](https://docs.pydantic.dev/)** 2.5.3 — Data validation with Python type hints
- **[structlog](https://www.structlog.org/)** 24.1.0 — Structured logging
- **[Uvicorn](https://www.uvicorn.org/)** 0.27.0 — ASGI server

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Simple health check, returns `{"status":"ok"}` |
| `GET` | `/api/v1/health` | Detailed health check with database and Redis status |
| `GET` | `/api/v1/streams` | List all active streams with pagination |
| `GET` | `/api/v1/streams/{id}/metrics` | Get aggregated metrics for a stream |
| `GET` | `/api/v1/streams/{id}/moments` | Get detected anomalies/moments for a stream |
| `WS` | `/ws/live/{stream_id}` | WebSocket for real-time metric streaming |

**Interactive API Docs:**
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Database Schema

The backend queries these PostgreSQL tables (created by `infra/init-db.sql`):

**`streams`**
- `stream_id` (VARCHAR, PK) — Unique stream identifier
- `title` (TEXT) — Stream title
- `created_at` (TIMESTAMP) — Creation timestamp
- `updated_at` (TIMESTAMP) — Last update timestamp

**`chat_summary_minute`**
- `id` (SERIAL, PK) — Auto-increment ID
- `stream_id` (VARCHAR) — Foreign key to streams
- `window_start` (TIMESTAMP) — Aggregation window start
- `window_end` (TIMESTAMP) — Aggregation window end
- `chat_count` (INTEGER) — Total messages in window
- `unique_chatters` (INTEGER) — Distinct users
- `top_emotes` (TEXT[]) — Most used emotes
- `avg_sentiment` (DOUBLE PRECISION) — Average sentiment score
- `chat_rate` (DOUBLE PRECISION) — Messages per second
- `avg_viewers` (DOUBLE PRECISION) — Average viewer count
- `z_score` (DOUBLE PRECISION) — Anomaly score
- `is_anomaly` (BOOLEAN) — Anomaly flag

**`moments`**
- `moment_id` (VARCHAR, PK) — Unique moment identifier
- `stream_id` (VARCHAR) — Foreign key to streams
- `timestamp` (TIMESTAMP) — When moment was detected
- `moment_type` (VARCHAR) — Type (chat_spike, viewer_spike, sentiment_shift)
- `description` (TEXT) — Human-readable description
- `metric_name` (VARCHAR) — Which metric triggered the moment
- `metric_value` (DOUBLE PRECISION) — Value at detection time
- `threshold` (DOUBLE PRECISION) — Threshold that was exceeded
- `z_score` (DOUBLE PRECISION) — Z-score value
- `metadata` (JSONB) — Additional metadata

**`viewer_timeseries`**, **`transactions`** — Additional tables for future features

---

## Environment Variables

Required variables (copy from `.env.example`):

```bash
# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=telemetra_dev_password
POSTGRES_DB=telemetra

# Redis
REDIS_URL=redis://redis:6379

# Kafka (optional, for future features)
KAFKA_BOOTSTRAP_SERVERS=kafka:29092

# API Configuration
API_TITLE=Telemetra API
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
DEBUG=false
```

---

## Project Structure

```
backend/
├── api/
│   ├── __init__.py
│   ├── routes.py                 # REST API endpoints
│   └── websocket.py              # WebSocket handler
├── db/
│   ├── __init__.py
│   ├── database.py               # PostgreSQL client with connection pooling
│   └── redis_client.py           # Redis client for caching
├── models/
│   ├── __init__.py
│   └── schemas.py                # Pydantic models for validation
├── tests/
│   ├── conftest.py               # Pytest fixtures
│   ├── test_api.py               # API endpoint tests
│   ├── test_health.py            # Health check tests
│   └── test_websocket.py         # WebSocket tests
├── __init__.py
├── main.py                        # FastAPI application entry point
├── config.py                      # Configuration management
├── Dockerfile                     # Multi-stage Docker build
├── entrypoint.sh                  # Startup script with dependency checks
└── requirements.txt               # Python dependencies
```

---

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use Docker Compose)
- Redis 7+ (or use Docker Compose)

### Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file (edit with local database credentials)
cp .env.example .env

# Run locally (requires PostgreSQL and Redis running)
python -m backend.main

# Or use uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Access:**
- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Testing

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run in Docker Compose
docker compose -f ../infra/docker-compose.yml exec backend pytest /app/tests -v
```

---

## Docker Deployment

The backend is containerized with a multi-stage Dockerfile for optimal image size.

```bash
# Build image
docker build -t telemetra-backend .

# Run container
docker run -p 8000:8000 --env-file .env telemetra-backend

# Or use Docker Compose (recommended)
docker compose -f ../infra/docker-compose.yml up backend -d
```

---

## Features

⚙️ **Async I/O**
- Non-blocking database queries with asyncpg
- Async Redis operations
- Concurrent request handling with ASGI

📊 **Caching Strategy**
- Redis cache-aside pattern
- TTL: 60s for metrics, 300s for streams list
- Automatic cache invalidation

🔗 **WebSocket Streaming**
- Real-time metric updates every 1-2 seconds
- Auto-reconnect support for clients
- Connection manager for multiple concurrent clients

🧩 **Observability**
- Structured logging with structlog
- Health checks for all dependencies
- OpenAPI documentation auto-generated

---

## Testing

**Test Coverage: 35+ test cases**

- `test_health.py` — Health check endpoints
- `test_api.py` — REST API endpoints (streams, metrics, moments)
- `test_websocket.py` — WebSocket connection, messaging, disconnect handling

**Run Tests:**

```bash
# All tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=backend --cov-report=term --cov-report=html

# Specific test
pytest tests/test_api.py::test_list_streams -v
```

---

## Performance

- **Connection Pooling:** 5-20 PostgreSQL connections (configurable)
- **Caching:** Sub-millisecond Redis responses
- **Async WebSocket:** Supports 100+ concurrent connections
- **Response Times:** <50ms for cached endpoints, <200ms for database queries

---

## Troubleshooting

**Database Connection Failed**

```bash
# Check PostgreSQL is running
docker compose -f ../infra/docker-compose.yml ps postgres

# Verify credentials in .env
# Test connection manually
docker compose -f ../infra/docker-compose.yml exec postgres psql -U telemetra -d telemetra
```

**Redis Connection Failed**

```bash
# Check Redis is running
docker compose -f ../infra/docker-compose.yml ps redis

# Test connection
docker compose -f ../infra/docker-compose.yml exec redis redis-cli PING
```

**Backend Won't Start**

```bash
# Check logs
docker compose -f ../infra/docker-compose.yml logs backend

# Restart backend
docker compose -f ../infra/docker-compose.yml restart backend
```

---

🔙 [Back to main README](../README.md)
