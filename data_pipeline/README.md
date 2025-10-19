<div align="center">

# ⚡ Telemetra — Data Pipeline

### Real-time Event Processing with Kafka and Spark Streaming

_Distributed stream processing for instant analytics_

<p align="center">
  <img src="https://img.shields.io/badge/Apache_Kafka-7.5.0-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white" alt="Kafka"/>
  <img src="https://img.shields.io/badge/Apache_Spark-3.5.0-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white" alt="Spark"/>
  <img src="https://img.shields.io/badge/PySpark-3.5.0-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white" alt="PySpark"/>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
</p>

<p align="center" style="font-weight: bold;">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-kafka-topics">Kafka Topics</a> •
  <a href="#-spark-streaming">Spark Processing</a> •
  <a href="#-components">Components</a>
</p>

[← Back to main README](../README.md)

</div>

---

## 📖 Overview

The Telemetra data pipeline ingests streaming events from **Apache Kafka**, processes them with **Apache Spark Streaming**, and writes aggregated metrics to PostgreSQL. It demonstrates modern stream processing patterns with windowed aggregations, sentiment analysis, and anomaly detection.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 📨 Event Ingestion

- ✅ Real-time event ingestion via Kafka
- ✅ 4 topics: chat, viewer, transactions, stream_meta
- ✅ JSON schema validation
- ✅ Configurable event generation rate

### ⚡ Stream Processing

- ✅ 1-minute tumbling windows
- ✅ 10-second sliding windows
- ✅ Windowed aggregations (count, avg, top-N)
- ✅ Join operations across streams

</td>
<td width="50%">

### 🧠 Analytics

- ✅ Lexicon-based sentiment analysis
- ✅ Z-score anomaly detection
- ✅ Top emote tracking
- ✅ Unique user counting

### 🗄️ Data Output

- ✅ JDBC writes to PostgreSQL
- ✅ Redis cache updates
- ✅ Checkpoint management
- ✅ Exactly-once semantics

</td>
</tr>
</table>

---

## 🚀 Quick Start

### 📋 Prerequisites

<p>
<img src="https://img.shields.io/badge/Docker-20.10+-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker 20.10+"/>
<img src="https://img.shields.io/badge/RAM-8GB-orange?style=flat-square" alt="8GB RAM"/>
</p>

### ⏱️ Start Data Pipeline

```bash
# Start all pipeline services
docker compose -f ../infra/docker-compose.yml up \
  zookeeper kafka mock-producer spark-master spark-worker spark-streaming-job -d

# Wait for services to initialize (30-60 seconds)
sleep 60

# Verify Kafka topics were created
docker compose -f ../infra/docker-compose.yml exec kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092
```

### ✔️ Verify Pipeline

**1. Check producer is generating events:**

```bash
docker compose -f ../infra/docker-compose.yml logs -f mock-producer
# Should see: "Sent chat message", "Sent viewer count", etc.
```

**2. Check Kafka has messages:**

```bash
docker compose -f ../infra/docker-compose.yml exec kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --from-beginning \
  --max-messages 5
```

**3. Check Spark job is processing:**

```bash
docker compose -f ../infra/docker-compose.yml logs -f spark-streaming-job
# Should see: "Batch: X", "Processing micro-batch", etc.
```

**4. Check data is written to PostgreSQL:**

```bash
docker compose -f ../infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra -c "SELECT COUNT(*) FROM chat_summary_minute;"
# Expected: count > 0 (after 2-3 minutes)
```

---

## 📨 Kafka Topics

### Topic Configuration

<table>
<tr>
<th>Topic</th>
<th>Partitions</th>
<th>Retention</th>
<th>Purpose</th>
</tr>
<tr>
<td><code>telemetra.events.chat</code></td>
<td>3</td>
<td>168h (7d)</td>
<td>Chat messages with emotes</td>
</tr>
<tr>
<td><code>telemetra.events.viewer</code></td>
<td>1</td>
<td>168h (7d)</td>
<td>Viewer count snapshots</td>
</tr>
<tr>
<td><code>telemetra.events.transactions</code></td>
<td>1</td>
<td>168h (7d)</td>
<td>Subscription/donation events</td>
</tr>
<tr>
<td><code>telemetra.events.stream_meta</code></td>
<td>1</td>
<td>168h (7d)</td>
<td>Stream title and metadata</td>
</tr>
</table>

### Topic Commands

<details>
<summary><b>📋 List topics</b></summary>

```bash
docker compose -f ../infra/docker-compose.yml exec kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092
```

</details>

<details>
<summary><b>📊 Describe topic</b></summary>

```bash
docker compose -f ../infra/docker-compose.yml exec kafka kafka-topics.sh \
  --describe --topic telemetra.events.chat --bootstrap-server localhost:9092
```

</details>

<details>
<summary><b>📭 Consume messages</b></summary>

```bash
docker compose -f ../infra/docker-compose.yml exec kafka kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --from-beginning \
  --max-messages 10
```

</details>

---

## ⚡ Spark Streaming Job

### Processing Logic

**1. Windowed Aggregations**

```python
windowed_chat = chat_df \
  .withWatermark("timestamp", "2 minutes") \
  .groupBy(
    window("timestamp", "1 minute", "10 seconds"),
    "stream_id"
  ) \
  .agg(
    count("message").alias("chat_count"),
    countDistinct("user_id").alias("unique_chatters"),
    collect_list("emotes").alias("all_emotes"),
    avg("sentiment_score").alias("avg_sentiment")
  )
```

**2. Sentiment Analysis**

- Lexicon-based scoring with positive/negative word lists
- Normalized by word count
- Sentiment range: -1.0 (negative) to +1.0 (positive)

**3. Anomaly Detection**

- Calculate Z-score for chat rate and viewer count
- Flag anomalies when |z_score| > 3.0 (3 standard deviations)
- Generate moment records for significant events

### Spark UI

Monitor job performance at:

- **Spark Master:** http://localhost:8080
- **Spark Worker:** http://localhost:8081

---

## 🎯 Components

### 1. Mock Producer

Generates realistic Twitch-like streaming events for testing.

**Configuration:**

```bash
# Event generation rate (messages per second)
PRODUCER_RATE_PER_SEC=10

# Comma-separated list of stream IDs
PRODUCER_CHANNELS=demo_stream,gaming_stream,music_stream

# Kafka bootstrap servers
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
```

**Run:**

```bash
docker compose -f ../infra/docker-compose.yml up mock-producer -d
docker compose -f ../infra/docker-compose.yml logs -f mock-producer
```

### 2. Spark Streaming Job

PySpark application that consumes Kafka events and performs real-time analytics.

**Features:**

- Consumes from 4 Kafka topics
- 1-minute tumbling windows with 10-second slides
- Lexicon-based sentiment analysis
- Z-score anomaly detection
- JDBC writes to PostgreSQL
- Redis cache updates

---

## 🛠️ Tech Stack

<p>
<img src="https://img.shields.io/badge/Apache_Kafka-7.5.0-231F20?style=for-the-badge&logo=apache-kafka&logoColor=white" alt="Kafka"/>
<img src="https://img.shields.io/badge/Apache_Spark-3.5.0-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white" alt="Spark"/>
<img src="https://img.shields.io/badge/PySpark-3.5.0-E25A1C?style=for-the-badge&logo=apache-spark&logoColor=white" alt="PySpark"/>
<img src="https://img.shields.io/badge/Zookeeper-3.8.3-000000?style=for-the-badge" alt="Zookeeper"/>
<img src="https://img.shields.io/badge/kafka_python-2.0.2-231F20?style=for-the-badge" alt="kafka-python"/>
</p>

---

## ⚙️ Configuration

### Environment Variables

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_LOG_RETENTION_HOURS=168       # 7 days
KAFKA_NUM_PARTITIONS=3

# Producer Configuration
PRODUCER_RATE_PER_SEC=10
PRODUCER_CHANNELS=demo_stream

# Spark Configuration
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_EXECUTOR_MEMORY=1g
SPARK_EXECUTOR_CORES=1
SPARK_DRIVER_MEMORY=1g

# Database Configuration
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=telemetra
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=telemetra_dev_password

# Redis Configuration
REDIS_URL=redis://redis:6379
```

---

## 🔧 Troubleshooting

<details>
<summary><b>📭 No Messages in Kafka</b></summary>

```bash
# Check producer is running
docker compose -f ../infra/docker-compose.yml ps mock-producer

# View producer logs
docker compose -f ../infra/docker-compose.yml logs mock-producer

# Verify topics exist
docker compose -f ../infra/docker-compose.yml exec kafka kafka-topics.sh \
  --list --bootstrap-server localhost:9092
```

</details>

<details>
<summary><b>⚡ Spark Job Not Processing</b></summary>

```bash
# Check Spark services are running
docker compose -f ../infra/docker-compose.yml ps | grep spark

# View Spark streaming job logs
docker compose -f ../infra/docker-compose.yml logs spark-streaming-job

# Check Spark Master UI
open http://localhost:8080
```

</details>

<details>
<summary><b>🗄️ Data Not Written to PostgreSQL</b></summary>

```bash
# Check Spark job logs for errors
docker compose -f ../infra/docker-compose.yml logs spark-streaming-job | grep ERROR

# Verify PostgreSQL is running
docker compose -f ../infra/docker-compose.yml ps postgres

# Check table exists
docker compose -f ../infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra -c "\dt"
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
<h3><a href="../infra/README.md">🐳 Infrastructure</a></h3>
<p>Docker services</p>
</td>
</tr>
</table>

</div>

---

<div align="center">

**Powered by Kafka** 📨 | **Processed by Spark** ⚡

[← Back to main README](../README.md)

</div>
