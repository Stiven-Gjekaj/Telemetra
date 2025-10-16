# Telemetra Data Pipeline - Quick Start Guide

Complete guide to getting the Telemetra data pipeline up and running.

## Overview

The Telemetra data pipeline consists of:

1. **Mock Producer** (`producer/`): Generates realistic Twitch-like streaming data
2. **Kafka Topics**: Message queues for event streaming
3. **Spark Streaming** (`spark/`): Real-time data processing and aggregation
4. **Schemas** (`schemas/`): JSON schema definitions for all message types

## Prerequisites

- Docker & Docker Compose (recommended)
- OR Python 3.12+ with Kafka and Spark installed locally

## Quick Start with Docker Compose

### 1. Start Infrastructure

The producer requires Kafka to be running. Add this to your `infra/docker-compose.yml`:

```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    networks:
      - telemetra-network

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 10s
      timeout: 10s
      retries: 5
    networks:
      - telemetra-network

  # Include the producer service
  twitch-producer:
    build:
      context: ../data_pipeline/producer
    depends_on:
      kafka:
        condition: service_healthy
    environment:
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      CHANNELS: demo_stream,gaming_channel
      RATE_PER_SEC: 20
      LOG_LEVEL: INFO
    networks:
      - telemetra-network

networks:
  telemetra-network:
    driver: bridge
```

### 2. Start Services

```bash
# From the infra directory
docker compose up -d

# Watch producer logs
docker compose logs -f twitch-producer

# Watch Kafka topics
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --from-beginning
```

### 3. Verify Data Flow

```bash
# Check all topics have messages
for topic in telemetra.events.chat telemetra.events.viewer telemetra.events.transactions telemetra.events.stream_meta; do
  echo "Checking $topic..."
  docker compose exec kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic $topic \
    --max-messages 5 \
    --from-beginning
done
```

## Quick Start without Docker

### 1. Start Kafka Locally

```bash
# Start Zookeeper
bin/zookeeper-server-start.sh config/zookeeper.properties

# Start Kafka (in another terminal)
bin/kafka-server-start.sh config/server.properties
```

### 2. Install Producer Dependencies

```bash
cd data_pipeline/producer
pip install -r requirements.txt
```

### 3. Run Producer

```bash
# Set environment variables
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export CHANNELS=demo_stream
export RATE_PER_SEC=10

# Run producer
python twitch_mock_producer.py
```

### 4. Test with Consumer

```bash
# In another terminal
cd data_pipeline/producer
python test_consumer.py
```

## Configuration

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address(es) | `kafka:9092` | `localhost:9092` |
| `CHANNELS` | Comma-separated channel list | `demo_stream` | `demo_stream,gaming,talk` |
| `RATE_PER_SEC` | Messages per second | `10` | `50` |
| `MESSAGE_VARIANTS` | Template variety | `50` | `100` |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG` |

### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `PRODUCE_CHAT` | Enable chat messages | `true` |
| `PRODUCE_VIEWER` | Enable viewer counts | `true` |
| `PRODUCE_TRANSACTIONS` | Enable transactions | `true` |
| `PRODUCE_STREAM_META` | Enable metadata events | `true` |

## Kafka Topics

### Created Automatically

The producer creates these topics on startup:

- `telemetra.events.chat` - Chat messages (3 partitions)
- `telemetra.events.viewer` - Viewer counts (3 partitions)
- `telemetra.events.transactions` - Monetization events (3 partitions)
- `telemetra.events.stream_meta` - Stream metadata (3 partitions)

### Manual Topic Management

```bash
# List all topics
kafka-topics --bootstrap-server localhost:9092 --list

# Describe a topic
kafka-topics --bootstrap-server localhost:9092 \
  --describe --topic telemetra.events.chat

# Delete a topic (if needed)
kafka-topics --bootstrap-server localhost:9092 \
  --delete --topic telemetra.events.chat

# Change topic configuration
kafka-configs --bootstrap-server localhost:9092 \
  --alter --entity-type topics \
  --entity-name telemetra.events.chat \
  --add-config retention.ms=604800000  # 7 days
```

## Monitoring

### Producer Metrics

The producer logs statistics every 100 messages:

```
2025-10-16 10:30:15 - INFO - Produced 100 messages | Actual rate: 10.2 msg/sec
2025-10-16 10:30:15 - INFO - Total by topic: {
  'telemetra.events.chat': 70,
  'telemetra.events.viewer': 20,
  'telemetra.events.transactions': 5,
  'telemetra.events.stream_meta': 5
}
```

### Kafka Consumer Groups

```bash
# List consumer groups
kafka-consumer-groups --bootstrap-server localhost:9092 --list

# Describe group lag
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --describe --group your-consumer-group
```

### Message Rate Monitoring

```bash
# Monitor messages per second
kafka-run-class kafka.tools.GetOffsetShell \
  --broker-list localhost:9092 \
  --topic telemetra.events.chat \
  --time -1
```

## Common Operations

### Increase Load

```bash
# Generate high-volume traffic
docker compose up -d --scale twitch-producer=3

# Or with environment variable
docker compose run -e RATE_PER_SEC=100 twitch-producer
```

### Change Channels

```bash
# Update in docker-compose.yml or:
docker compose run \
  -e CHANNELS=gaming,esports,music,cooking \
  twitch-producer
```

### View Live Messages

```bash
# Pretty-print JSON messages
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --from-beginning | jq .
```

### Reset Offsets

```bash
# Reset consumer group to beginning
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --group your-group \
  --reset-offsets --to-earliest \
  --topic telemetra.events.chat \
  --execute
```

## Troubleshooting

### Producer Can't Connect to Kafka

**Symptoms**: `Connection refused` or `Connection timeout` errors

**Solutions**:
1. Verify Kafka is running: `docker compose ps kafka`
2. Check Kafka health: `docker compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092`
3. Verify network connectivity: `docker compose exec twitch-producer ping kafka`
4. Check `KAFKA_BOOTSTRAP_SERVERS` environment variable

### No Messages in Topics

**Symptoms**: Consumer shows no messages

**Solutions**:
1. Check producer logs: `docker compose logs twitch-producer`
2. List topics: `docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092`
3. Check topic has data: `kafka-console-consumer --from-beginning --max-messages 1`
4. Verify producer is running: `docker compose ps twitch-producer`

### High Memory Usage

**Symptoms**: Producer container using excessive memory

**Solutions**:
1. Reduce `RATE_PER_SEC` value
2. Reduce number of `CHANNELS`
3. Set resource limits in docker-compose.yml:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 256M
   ```

### Messages Not Balanced Across Partitions

**Symptoms**: All messages going to one partition

**Solutions**:
1. Verify key-based partitioning is working (using channel as key)
2. Increase number of partitions if needed
3. Check Kafka partition assignment logs

## Performance Tuning

### For High Throughput

```yaml
environment:
  RATE_PER_SEC: 1000
  # Kafka producer settings (in code)
  # batch.size: 32768
  # linger.ms: 20
  # compression.type: lz4
```

### For Low Latency

```yaml
environment:
  RATE_PER_SEC: 10
  # Kafka producer settings (in code)
  # batch.size: 1
  # linger.ms: 0
  # acks: 1
```

### For Resource-Constrained Environments

```yaml
environment:
  RATE_PER_SEC: 5
  CHANNELS: demo_stream  # Single channel only
deploy:
  resources:
    limits:
      cpus: '0.25'
      memory: 128M
```

## Next Steps

1. **Integrate Spark Processing**: See `spark/QUICKSTART.md`
2. **Connect Backend**: Configure backend to read from Kafka topics
3. **Add Monitoring**: Set up Prometheus and Grafana
4. **Schema Registry**: Integrate Confluent Schema Registry for schema evolution

## Useful Commands

```bash
# View all producer logs
docker compose logs -f twitch-producer

# Restart producer with new config
docker compose restart twitch-producer

# Stop producer gracefully
docker compose stop twitch-producer

# View producer resource usage
docker stats telemetra-twitch-producer

# Execute command in producer container
docker compose exec twitch-producer bash

# Tail specific topic
docker compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.transactions \
  --property print.timestamp=true \
  --property print.key=true
```

## Resources

- [Producer README](producer/README.md) - Detailed producer documentation
- [Schema Documentation](schemas/README.md) - Message schema details
- [Confluent Kafka Python Docs](https://docs.confluent.io/kafka-clients/python/current/overview.html)
- [Kafka Operations Guide](https://kafka.apache.org/documentation/#operations)
