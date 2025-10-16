# Telemetra — Data Pipeline

[![CI](https://img.shields.io/github/actions/workflow/status/Stiven-Gjekaj/Telemetra/ci.yml?branch=main&label=CI)](https://github.com/Stiven-Gjekaj/Telemetra/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)

[← Back to main README](../README.md)

---

## Overview

The Telemetra data pipeline ingests streaming events from Kafka, processes them with Spark Streaming, and writes aggregated metrics to PostgreSQL.

**Data Flow:**
```
Mock Producer → Kafka (4 topics) → Spark Streaming → PostgreSQL + Redis
```

---

## Components

### Mock Producer
Generates realistic Twitch-like streaming data for testing.
- Topics: chat, viewer, transactions, stream_meta
- Configurable rate (default: 10 msg/sec)

### Spark Streaming Job
PySpark application performing real-time processing:
- 1-minute tumbling windows with 10-second slides
- Sentiment analysis (lexicon-based)
- Z-score anomaly detection (threshold: 3.0σ)
- JDBC writes to PostgreSQL

---

## Running

```bash
# Start producer
docker compose -f ../infra/docker-compose.yml up mock-producer -d

# Start Spark job
docker compose -f ../infra/docker-compose.yml up spark-streaming-job -d
```

---

🔙 [Back to main README](../README.md)
