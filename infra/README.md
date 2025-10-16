# Telemetra — Infrastructure

[![CI](https://img.shields.io/github/actions/workflow/status/Stiven-Gjekaj/Telemetra/ci.yml?branch=main&label=CI)](https://github.com/Stiven-Gjekaj/Telemetra/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-20.10+-blue.svg)](https://www.docker.com/)

[← Back to main README](../README.md)

---

## Overview

Telemetra infrastructure is fully containerized with Docker Compose, orchestrating 15 services with health checks and resource limits.

---

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Zookeeper | 2181 | Kafka coordination |
| Kafka | 9092 | Event streaming |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache layer |
| Spark Master | 7077, 8080 | Distributed computing |
| Spark Worker | 8081 | Task execution |
| Backend | 8000 | REST API + WebSocket |
| Frontend | 3000 | Web dashboard |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3001 | Visualization |

---

## Quick Start

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml --profile dev up -d
```

---

## Monitoring

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

---

🔙 [Back to main README](../README.md)
