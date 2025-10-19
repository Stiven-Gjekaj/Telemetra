<div align="center">

# 🐳 Telemetra — Infrastructure

### Fully Containerized Deployment with Docker Compose

_Orchestrating 15 microservices with health checks and monitoring_

<p align="center">
  <img src="https://img.shields.io/badge/Docker-20.10+-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/Docker_Compose-1.29+-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose"/>
  <img src="https://img.shields.io/badge/Prometheus-2.48-E6522C?style=for-the-badge&logo=prometheus&logoColor=white" alt="Prometheus"/>
  <img src="https://img.shields.io/badge/Grafana-10.2-F46800?style=for-the-badge&logo=grafana&logoColor=white" alt="Grafana"/>
</p>

<p align="center" style="font-weight: bold;">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-services">Services</a> •
  <a href="#-docker-profiles">Profiles</a> •
  <a href="#-monitoring">Monitoring</a>
</p>

[← Back to main README](../README.md)

</div>

---

## 📖 Overview

Telemetra infrastructure is fully containerized with **Docker Compose**, orchestrating 15 microservices with health checks, resource limits, and automated dependency management. The platform demonstrates production-ready practices with monitoring, observability, and horizontal scaling capabilities.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🐳 Container Orchestration

- ✅ 15 containerized services
- ✅ Health checks for all services
- ✅ Resource limits (CPU, memory)
- ✅ Automatic restart policies

### 🌐 Networking

- ✅ Internal Docker network
- ✅ DNS-based service discovery
- ✅ Network isolation
- ✅ Custom subnet management

</td>
<td width="50%">

### 💾 Data Persistence

- ✅ Persistent Docker volumes
- ✅ Data backup support
- ✅ Volume management
- ✅ Stateful services support

### 📈 Monitoring

- ✅ Prometheus metrics collection
- ✅ Grafana dashboards
- ✅ Service health tracking
- ✅ Real-time observability

</td>
</tr>
</table>

---

## 🚀 Quick Start

### 📋 Prerequisites

<p>
<img src="https://img.shields.io/badge/Docker-20.10+-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker 20.10+"/>
<img src="https://img.shields.io/badge/RAM-8GB-orange?style=flat-square" alt="8GB RAM"/>
<img src="https://img.shields.io/badge/Disk-20GB-blue?style=flat-square" alt="20GB Disk"/>
</p>

### ⏱️ Start All Services

**Development Profile (Recommended):**

```bash
# Copy environment configuration
cp .env.example .env

# Start core services + monitoring (10 services)
docker compose -f infra/docker-compose.yml --profile dev up -d

# Wait for services to initialize
sleep 120

# Verify all services are running
docker compose -f infra/docker-compose.yml ps
```

**Full Profile (All services including management UIs):**

```bash
# Start all 15 services
docker compose -f infra/docker-compose.yml --profile full --profile dev up -d
```

### ✔️ Verify Services

```bash
# Check service status
docker compose -f infra/docker-compose.yml ps

# Quick health checks
curl http://localhost:8000/health     # Backend
curl http://localhost:3000            # Frontend
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3001/api/health # Grafana
```

---

## 🐳 Services

### Core Services (Always Running)

<table>
<tr>
<th>Service</th>
<th>Image</th>
<th>Purpose</th>
<th>Profile</th>
</tr>
<tr>
<td><b>zookeeper</b></td>
<td>confluentinc/cp-zookeeper:7.5.0</td>
<td>Kafka coordination</td>
<td>dev, full</td>
</tr>
<tr>
<td><b>kafka</b></td>
<td>confluentinc/cp-kafka:7.5.0</td>
<td>Event streaming</td>
<td>dev, full</td>
</tr>
<tr>
<td><b>postgres</b></td>
<td>postgres:15-alpine</td>
<td>Primary database</td>
<td>dev, full</td>
</tr>
<tr>
<td><b>redis</b></td>
<td>redis:7-alpine</td>
<td>Cache layer</td>
<td>dev, full</td>
</tr>
<tr>
<td><b>spark-master</b></td>
<td>bitnami/spark:3.5.0</td>
<td>Distributed computing</td>
<td>dev, full</td>
</tr>
<tr>
<td><b>spark-worker</b></td>
<td>bitnami/spark:3.5.0</td>
<td>Task execution</td>
<td>dev, full</td>
</tr>
<tr>
<td><b>backend</b></td>
<td>Custom (FastAPI)</td>
<td>REST API + WebSocket</td>
<td>dev, full</td>
</tr>
<tr>
<td><b>frontend</b></td>
<td>Custom (React + Nginx)</td>
<td>Web dashboard</td>
<td>dev, full</td>
</tr>
</table>

### Processing Services

| Service                   | Image             | Purpose              | Profile   |
| ------------------------- | ----------------- | -------------------- | --------- |
| **mock-producer**         | Custom (Python)   | Event generator      | dev, full |
| **spark-streaming-job**   | Custom (PySpark)  | Real-time processing | dev, full |

### Monitoring Services

| Service        | Image                     | Purpose                 | Profile   |
| -------------- | ------------------------- | ----------------------- | --------- |
| **prometheus** | prom/prometheus:v2.48.0   | Metrics collection      | dev, full |
| **grafana**    | grafana/grafana:10.2.0    | Metrics visualization   | dev, full |

### Management Services (Optional)

| Service      | Image                       | Purpose                 | Profile |
| ------------ | --------------------------- | ----------------------- | ------- |
| **kafka-ui** | provectuslabs/kafka-ui      | Kafka management UI     | full    |
| **pgadmin**  | dpage/pgadmin4              | PostgreSQL management   | full    |

---

## 🌐 Service Ports

### External Access Ports

<table>
<tr>
<th>Service</th>
<th>Port</th>
<th>URL</th>
<th>Profile</th>
</tr>
<tr>
<td><b>Frontend</b></td>
<td>3000</td>
<td><a href="http://localhost:3000">http://localhost:3000</a></td>
<td>dev, full</td>
</tr>
<tr>
<td><b>Backend API</b></td>
<td>8000</td>
<td><a href="http://localhost:8000">http://localhost:8000</a></td>
<td>dev, full</td>
</tr>
<tr>
<td><b>API Docs</b></td>
<td>8000</td>
<td><a href="http://localhost:8000/docs">http://localhost:8000/docs</a></td>
<td>dev, full</td>
</tr>
<tr>
<td><b>Prometheus</b></td>
<td>9090</td>
<td><a href="http://localhost:9090">http://localhost:9090</a></td>
<td>dev, full</td>
</tr>
<tr>
<td><b>Grafana</b></td>
<td>3001</td>
<td><a href="http://localhost:3001">http://localhost:3001</a></td>
<td>dev, full</td>
</tr>
<tr>
<td><b>Spark Master UI</b></td>
<td>8080</td>
<td><a href="http://localhost:8080">http://localhost:8080</a></td>
<td>dev, full</td>
</tr>
<tr>
<td><b>Kafka UI</b></td>
<td>8888</td>
<td><a href="http://localhost:8888">http://localhost:8888</a></td>
<td>full</td>
</tr>
<tr>
<td><b>pgAdmin</b></td>
<td>5050</td>
<td><a href="http://localhost:5050">http://localhost:5050</a></td>
<td>full</td>
</tr>
</table>

---

## 🎯 Docker Profiles

### `dev` Profile (Recommended for Development)

**Services:** 10 core services

- All data pipeline services (Kafka, Spark, Producer)
- Backend API + Frontend
- Database + Cache (PostgreSQL, Redis)
- Monitoring (Prometheus, Grafana)

**Start:**

```bash
docker compose -f infra/docker-compose.yml --profile dev up -d
```

**Resource Usage:**

- Memory: ~8-10GB
- CPU: 0.5-1.0 (idle)
- Disk: ~5GB

### `full` Profile (All Services)

**Services:** All 15 services (dev + management tools)

- Everything from dev profile
- Kafka UI (port 8888)
- pgAdmin (port 5050)

**Start:**

```bash
docker compose -f infra/docker-compose.yml --profile full --profile dev up -d
```

**Resource Usage:**

- Memory: ~10-12GB
- CPU: 0.7-1.2 (idle)
- Disk: ~7GB

---

## 📈 Monitoring

### Prometheus

**Access:** http://localhost:9090

**Key Metrics:**

- `http_requests_total` — HTTP request counts
- `postgres_connections` — Active database connections
- `redis_memory_used_bytes` — Redis memory usage
- `kafka_topics` — Kafka topic count

### Grafana

**Access:** http://localhost:3001

**Default Credentials:**

- Username: `admin`
- Password: `admin`

**Pre-configured Dashboards:**

- **Telemetra Overview** — System health and key metrics
- **Kafka Monitoring** — Topic throughput and consumer lag
- **Spark Performance** — Job execution and resource usage
- **Database Performance** — Query times and connection pools

---

## ⚙️ Configuration

### Environment Variables

Edit `.env` to customize:

```bash
# Database Configuration
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=telemetra_dev_password
POSTGRES_DB=telemetra

# Redis Configuration
REDIS_PORT=6379
REDIS_MAXMEMORY=512mb

# Kafka Configuration
KAFKA_PORT=9092
KAFKA_LOG_RETENTION_HOURS=168

# Producer Configuration
PRODUCER_RATE_PER_SEC=10
PRODUCER_CHANNELS=demo_stream

# Spark Configuration
SPARK_EXECUTOR_MEMORY=1g
SPARK_DRIVER_MEMORY=1g

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin
```

---

## ⚙️ Common Operations

<details>
<summary><b>📝 View Logs</b></summary>

```bash
# All services
docker compose -f infra/docker-compose.yml logs -f

# Specific service
docker compose -f infra/docker-compose.yml logs -f backend
```

</details>

<details>
<summary><b>🔄 Restart Services</b></summary>

```bash
# Restart single service
docker compose -f infra/docker-compose.yml restart backend

# Rebuild and restart after code changes
docker compose -f infra/docker-compose.yml build backend --no-cache
docker compose -f infra/docker-compose.yml up backend -d
```

</details>

<details>
<summary><b>📊 Monitor Resources</b></summary>

```bash
# Real-time resource usage
docker stats

# Filter by service
docker stats $(docker compose -f infra/docker-compose.yml ps -q)
```

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>🚪 Port Already in Use</b></summary>

```bash
# Find process using port (Windows)
netstat -ano | findstr :8000

# Find process using port (Mac/Linux)
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

</details>

<details>
<summary><b>🐳 Service Won't Start</b></summary>

```bash
# Check service status
docker compose -f infra/docker-compose.yml ps

# View logs for errors
docker compose -f infra/docker-compose.yml logs <service_name>

# Restart service
docker compose -f infra/docker-compose.yml restart <service_name>
```

</details>

<details>
<summary><b>🔄 Clean Slate Reset</b></summary>

```bash
# Stop all services
docker compose -f infra/docker-compose.yml down

# Remove volumes (DELETES ALL DATA!)
docker compose -f infra/docker-compose.yml down -v

# Start fresh
docker compose -f infra/docker-compose.yml --profile dev up --build -d
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
<h3><a href="../backend/README.md">🔌 Backend</a></h3>
<p>FastAPI service</p>
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

**Built with Docker** 🐳 | **Powered by Docker Compose** 🚀

[← Back to main README](../README.md)

</div>
