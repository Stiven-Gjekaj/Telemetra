<div align="center">

# 🔌 Telemetra — Backend

### FastAPI Service for Real-time Analytics

_REST endpoints and WebSocket streaming powered by async Python_

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.109.0-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
</p>

<p align="center" style="font-weight: bold;">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-api-endpoints">API Endpoints</a> •
  <a href="#️-database-schema">Database Schema</a> •
  <a href="#-features">Features</a>
</p>

[← Back to main README](../README.md)

</div>

---

## 📖 Overview

The Telemetra backend is a **FastAPI service** that provides REST endpoints and WebSocket streaming for real-time streaming analytics. It consumes aggregated metrics from PostgreSQL, caches frequently accessed data in Redis, and exposes a clean API for the frontend dashboard.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### ⚙️ Async I/O

- ✅ Non-blocking database queries with asyncpg
- ✅ Async Redis operations
- ✅ Concurrent request handling with ASGI
- ✅ Connection pooling for optimal resource usage

### 📊 Caching Strategy

- ✅ Cache-aside pattern with Redis
- ✅ TTL: 60s for metrics, 300s for streams
- ✅ Automatic cache invalidation
- ✅ Sub-millisecond response times

</td>
<td width="50%">

### 🔗 WebSocket Streaming

- ✅ Real-time metric updates (1-2 seconds)
- ✅ Auto-reconnect support for clients
- ✅ Connection manager for 100+ clients
- ✅ Graceful disconnect handling

### 🧩 Observability

- ✅ Structured logging with structlog
- ✅ Correlation IDs for request tracing
- ✅ Health checks for dependencies
- ✅ OpenAPI documentation auto-generated

</td>
</tr>
</table>

---

## 🚀 Quick Start

### 📋 Prerequisites

<p>
<img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+"/>
<img src="https://img.shields.io/badge/PostgreSQL-15+-316192?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL 15+"/>
<img src="https://img.shields.io/badge/Redis-7+-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis 7+"/>
</p>

### ⏱️ Local Development Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run locally (requires PostgreSQL and Redis running)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 🌐 Access Points

<table>
<tr>
<th>Service</th>
<th>URL</th>
<th>Purpose</th>
</tr>
<tr>
<td><b>API Root</b></td>
<td><a href="http://localhost:8000">http://localhost:8000</a></td>
<td>API base URL</td>
</tr>
<tr>
<td><b>Swagger UI</b></td>
<td><a href="http://localhost:8000/docs">http://localhost:8000/docs</a></td>
<td>Interactive API docs</td>
</tr>
<tr>
<td><b>ReDoc</b></td>
<td><a href="http://localhost:8000/redoc">http://localhost:8000/redoc</a></td>
<td>Alternative API docs</td>
</tr>
<tr>
<td><b>Health Check</b></td>
<td><a href="http://localhost:8000/health">http://localhost:8000/health</a></td>
<td>Simple health check</td>
</tr>
</table>

### ✔️ Verify Backend

```bash
# Simple health check
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Detailed health check
curl http://localhost:8000/api/v1/health
# Expected: {"status":"ok","database":"ok","redis":"ok"}
```

---

## 🔌 API Endpoints

### Health Checks

<table>
<tr>
<th>Method</th>
<th>Path</th>
<th>Description</th>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/health</code></td>
<td>Simple health check, returns <code>{"status":"ok"}</code></td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/v1/health</code></td>
<td>Detailed health check with database and Redis status</td>
</tr>
</table>

### Stream Endpoints

<table>
<tr>
<th>Method</th>
<th>Path</th>
<th>Description</th>
<th>Query Params</th>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/v1/streams</code></td>
<td>List all active streams with pagination</td>
<td><code>limit</code>, <code>offset</code></td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/v1/streams/{id}/metrics</code></td>
<td>Get aggregated metrics for a stream</td>
<td><code>limit</code>, <code>start_time</code>, <code>end_time</code></td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/v1/streams/{id}/moments</code></td>
<td>Get detected anomalies/moments for a stream</td>
<td><code>limit</code>, <code>moment_type</code></td>
</tr>
</table>

### WebSocket

<table>
<tr>
<th>Method</th>
<th>Path</th>
<th>Description</th>
</tr>
<tr>
<td><code>WS</code></td>
<td><code>/ws/live/{stream_id}</code></td>
<td>WebSocket for real-time metric streaming</td>
</tr>
</table>

---

## 🗄️ Database Schema

### PostgreSQL Tables

<details>
<summary><b>📋 <code>streams</code> Table</b></summary>

Stores active stream metadata

| Column        | Type           | Description                |
| ------------- | -------------- | -------------------------- |
| `stream_id`   | VARCHAR (PK)   | Unique stream identifier   |
| `title`       | TEXT           | Stream title               |
| `created_at`  | TIMESTAMP      | Creation timestamp         |
| `updated_at`  | TIMESTAMP      | Last update timestamp      |

</details>

<details>
<summary><b>💬 <code>chat_summary_minute</code> Table</b></summary>

Aggregated chat metrics per window

| Column             | Type              | Description                                  |
| ------------------ | ----------------- | -------------------------------------------- |
| `id`               | SERIAL (PK)       | Auto-increment ID                            |
| `stream_id`        | VARCHAR (FK)      | Foreign key to streams                       |
| `window_start`     | TIMESTAMP         | Aggregation window start                     |
| `window_end`       | TIMESTAMP         | Aggregation window end                       |
| `chat_count`       | INTEGER           | Total messages in window                     |
| `unique_chatters`  | INTEGER           | Distinct users                               |
| `top_emotes`       | TEXT[]            | Most used emotes (array)                     |
| `avg_sentiment`    | DOUBLE PRECISION  | Average sentiment score (-1 to 1)            |
| `chat_rate`        | DOUBLE PRECISION  | Messages per second                          |
| `avg_viewers`      | DOUBLE PRECISION  | Average viewer count                         |
| `z_score`          | DOUBLE PRECISION  | Anomaly score (Z-score)                      |
| `is_anomaly`       | BOOLEAN           | Anomaly flag (true if \|z_score\| > 3.0)     |

</details>

<details>
<summary><b>⚡ <code>moments</code> Table</b></summary>

Detected anomalies and significant events

| Column           | Type              | Description                                                 |
| ---------------- | ----------------- | ----------------------------------------------------------- |
| `moment_id`      | VARCHAR (PK)      | Unique moment identifier (UUID)                             |
| `stream_id`      | VARCHAR (FK)      | Foreign key to streams                                      |
| `timestamp`      | TIMESTAMP         | When moment was detected                                    |
| `moment_type`    | VARCHAR           | Type: `chat_spike`, `viewer_spike`, `sentiment_shift`       |
| `description`    | TEXT              | Human-readable description                                  |
| `metric_name`    | VARCHAR           | Which metric triggered detection                            |
| `metric_value`   | DOUBLE PRECISION  | Value at detection time                                     |
| `threshold`      | DOUBLE PRECISION  | Threshold that was exceeded                                 |
| `z_score`        | DOUBLE PRECISION  | Z-score value                                               |
| `metadata`       | JSONB             | Additional metadata (JSON)                                  |

</details>

---

## 🛠️ Tech Stack

<p>
<img src="https://img.shields.io/badge/FastAPI-0.109.0-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/Uvicorn-0.27.0-009688?style=for-the-badge" alt="Uvicorn"/>
<img src="https://img.shields.io/badge/asyncpg-0.29.0-316192?style=for-the-badge" alt="asyncpg"/>
<img src="https://img.shields.io/badge/Redis_Py-5.0.1-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis"/>
<img src="https://img.shields.io/badge/Pydantic-2.5.3-E92063?style=for-the-badge" alt="Pydantic"/>
<img src="https://img.shields.io/badge/structlog-24.1.0-00ADD8?style=for-the-badge" alt="structlog"/>
<img src="https://img.shields.io/badge/pytest-7.4.3-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" alt="pytest"/>
</p>

---

## 🐋 Docker Deployment

```bash
# Start backend service
docker compose -f ../infra/docker-compose.yml up backend -d

# View logs
docker compose -f ../infra/docker-compose.yml logs -f backend

# Restart after code changes
docker compose -f ../infra/docker-compose.yml build backend --no-cache
docker compose -f ../infra/docker-compose.yml restart backend
```

---

## 🧪 Testing

### Test Coverage: 35+ Test Cases

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=backend --cov-report=term --cov-report=html

# Run tests in Docker
docker compose -f ../infra/docker-compose.yml exec backend pytest /app/tests -v
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# PostgreSQL Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=your_password
POSTGRES_DB=telemetra

# Redis Configuration
REDIS_URL=redis://redis:6379

# API Configuration
API_TITLE=Telemetra API
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=INFO
DEBUG=false
```

---

## 🔧 Troubleshooting

<details>
<summary><b>🗄️ Database Connection Failed</b></summary>

```bash
# Check PostgreSQL is running
docker compose -f ../infra/docker-compose.yml ps postgres

# Test connection manually
docker compose -f ../infra/docker-compose.yml exec postgres psql -U telemetra -d telemetra
```

</details>

<details>
<summary><b>💾 Redis Connection Failed</b></summary>

```bash
# Check Redis is running
docker compose -f ../infra/docker-compose.yml ps redis

# Test connection
docker compose -f ../infra/docker-compose.yml exec redis redis-cli PING
```

</details>

<details>
<summary><b>🔌 Backend Won't Start</b></summary>

```bash
# Check backend logs for errors
docker compose -f ../infra/docker-compose.yml logs backend

# Restart backend service
docker compose -f ../infra/docker-compose.yml restart backend
```

</details>

---

## 📚 Additional Resources

<div align="center">

<table>
<tr>
<td align="center" width="33%">
<h3><a href="../README.md">🏠 Main README</a></h3>
<p>Project overview</p>
</td>
<td align="center" width="33%">
<h3><a href="../frontend/README.md">🎨 Frontend</a></h3>
<p>React dashboard</p>
</td>
<td align="center" width="33%">
<h3><a href="../data_pipeline/README.md">⚡ Pipeline</a></h3>
<p>Data processing</p>
</td>
</tr>
</table>

</div>

---

<div align="center">

**Built with FastAPI** ⚡ | **Powered by async Python** 🐍

[← Back to main README](../README.md)

</div>
