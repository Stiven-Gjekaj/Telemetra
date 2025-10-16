# Telemetra Data Pipeline

Real-time streaming data pipeline for the Telemetra MVP - processing Twitch-like streaming analytics.

## Architecture Overview

```
┌─────────────────┐
│ Mock Producer   │
│ (Twitch-like)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka Topics   │
│  - chat         │
│  - viewer       │
│  - transactions │
│  - stream_meta  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Spark Streaming │
│  (Aggregation)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│  (Time-series)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backend API    │
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Frontend       │
│  (React/D3)     │
└─────────────────┘
```

## Components

### 1. Producer (`producer/`)

**Purpose**: Generate realistic mock Twitch streaming data

**Key Files**:
- `twitch_mock_producer.py` - Main producer application (28KB, 734 lines)
- `test_consumer.py` - Testing utility (5.9KB, 188 lines)
- `Dockerfile` - Container image
- `requirements.txt` - Python dependencies
- `README.md` - Detailed documentation

**Features**:
- Realistic chat messages with emotes
- Dynamic viewer count simulation
- Transaction events (donations, subs, bits)
- Stream lifecycle events
- Configurable via environment variables
- Production-ready error handling

**Quick Start**:
```bash
cd producer
pip install -r requirements.txt
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
python twitch_mock_producer.py
```

### 2. Schemas (`schemas/`)

**Purpose**: JSON Schema definitions for all message types

**Files**:
- `chat_message.json` (2.6KB) - Chat message schema
- `viewer_count.json` (1.8KB) - Viewer count schema
- `transaction.json` (2.8KB) - Transaction schema
- `stream_meta.json` (2.9KB) - Stream metadata schema
- `validate_schema.py` - Validation utility
- `README.md` - Schema documentation

**Features**:
- JSON Schema Draft-07 compliant
- Comprehensive field validation
- Schema evolution guidelines
- Example messages

**Quick Start**:
```bash
cd schemas
python validate_schema.py chat_message.json '{"message_id": "...", ...}'
```

### 3. Spark Streaming (`spark/`)

**Purpose**: Real-time data processing and aggregation

**Key Files**:
- `spark_streaming_job.py` - Main Spark job
- `Dockerfile` - Spark container
- `requirements.txt` - PySpark dependencies
- `README.md` - Detailed documentation

**Features**:
- Windowed aggregations (1-minute windows)
- Sentiment analysis (lexicon-based)
- Anomaly detection (z-score)
- PostgreSQL integration via JDBC
- Configurable watermarking

**Quick Start**:
```bash
cd spark
pip install -r requirements.txt
spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  spark_streaming_job.py
```

## Kafka Topics

All topics use 3 partitions, partitioned by channel name:

| Topic | Purpose | Avg Rate | Message Size |
|-------|---------|----------|--------------|
| `telemetra.events.chat` | Chat messages | ~7 msg/sec | ~300 bytes |
| `telemetra.events.viewer` | Viewer counts | ~2 msg/sec | ~200 bytes |
| `telemetra.events.transactions` | Monetization | ~0.5 msg/sec | ~250 bytes |
| `telemetra.events.stream_meta` | Lifecycle events | ~0.5 msg/sec | ~300 bytes |

**Total**: ~10 messages/sec at default configuration (~2.5 KB/sec)

## Message Flow

### 1. Chat Message Flow

```
Producer → Kafka (telemetra.events.chat) → Spark → PostgreSQL
```

**Example**:
```json
{
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "channel": "demo_stream",
  "username": "gamer123",
  "message": "That was insane! PogChamp",
  "emotes": ["PogChamp"],
  "sentiment_hint": "excited",
  "timestamp": "2025-10-16T10:30:00Z"
}
```

### 2. Viewer Count Flow

```
Producer → Kafka (telemetra.events.viewer) → Spark → PostgreSQL
```

**Example**:
```json
{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "channel": "demo_stream",
  "viewer_count": 1234,
  "chatter_count": 123,
  "timestamp": "2025-10-16T10:30:00Z"
}
```

### 3. Transaction Flow

```
Producer → Kafka (telemetra.events.transactions) → Spark → PostgreSQL
```

**Example**:
```json
{
  "transaction_id": "txn_a1b2c3d4e5f6g7h8",
  "channel": "demo_stream",
  "transaction_type": "donation",
  "amount": 50.00,
  "timestamp": "2025-10-16T10:30:00Z"
}
```

### 4. Stream Metadata Flow

```
Producer → Kafka (telemetra.events.stream_meta) → Spark → PostgreSQL
```

**Example**:
```json
{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "channel": "demo_stream",
  "event_type": "stream_start",
  "title": "Chill vibes and good times",
  "timestamp": "2025-10-16T10:00:00Z"
}
```

## Quick Start Guide

### Prerequisites

- Docker & Docker Compose
- OR Python 3.12+ with Kafka and Spark

### Docker Compose (Recommended)

1. **Start infrastructure**:
   ```bash
   cd infra
   docker compose up -d
   ```

2. **Verify services**:
   ```bash
   docker compose ps
   docker compose logs -f twitch-producer
   ```

3. **Check data flow**:
   ```bash
   # View chat messages
   docker compose exec kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic telemetra.events.chat \
     --from-beginning --max-messages 10
   ```

### Local Development

1. **Start Kafka**:
   ```bash
   # Start Zookeeper
   bin/zookeeper-server-start.sh config/zookeeper.properties

   # Start Kafka
   bin/kafka-server-start.sh config/server.properties
   ```

2. **Run Producer**:
   ```bash
   cd data_pipeline/producer
   pip install -r requirements.txt
   export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   python twitch_mock_producer.py
   ```

3. **Run Spark Job** (in another terminal):
   ```bash
   cd data_pipeline/spark
   pip install -r requirements.txt
   spark-submit spark_streaming_job.py
   ```

## Configuration

### Environment Variables

#### Producer
```bash
KAFKA_BOOTSTRAP_SERVERS=kafka:9092    # Kafka broker
CHANNELS=demo_stream,gaming            # Channel list
RATE_PER_SEC=20                        # Message rate
LOG_LEVEL=INFO                         # Logging
```

#### Spark
```bash
KAFKA_BOOTSTRAP_SERVERS=kafka:9092     # Kafka broker
POSTGRES_HOST=postgres                 # Database
POSTGRES_PORT=5432                     # DB port
POSTGRES_DB=telemetra                  # Database name
POSTGRES_USER=telemetra                # DB user
POSTGRES_PASSWORD=secret               # DB password
CHECKPOINT_DIR=/tmp/spark-checkpoints  # Checkpointing
```

## Monitoring

### Producer Metrics

```bash
# View producer logs
docker compose logs -f twitch-producer

# Check message production rate
docker compose logs twitch-producer | grep "Actual rate"
```

### Kafka Metrics

```bash
# List topics
kafka-topics --bootstrap-server localhost:9092 --list

# Describe topic
kafka-topics --bootstrap-server localhost:9092 \
  --describe --topic telemetra.events.chat

# Consumer lag
kafka-consumer-groups --bootstrap-server localhost:9092 \
  --describe --group spark-streaming-consumer
```

### Spark Metrics

```bash
# View Spark logs
docker compose logs -f spark-streaming

# Spark UI (if running)
open http://localhost:4040
```

## Data Patterns

### Chat Messages
- **Rate**: ~70% of total messages
- **Emotes**: 23 popular emotes (Kappa, PogChamp, LUL, etc.)
- **Sentiment**: positive, negative, neutral, excited, question
- **Badges**: subscriber, moderator, VIP, partner

### Viewer Counts
- **Rate**: ~20% of total messages
- **Pattern**: Random walk with occasional spikes/drops
- **Range**: 100-5000 viewers
- **Chatter Ratio**: 5-20% of viewers

### Transactions
- **Rate**: ~5% of total messages
- **Types**: donation, subscription, bits, gift_sub
- **Amounts**: $1-$500 (donations), Tier 1-3 (subs)

### Stream Metadata
- **Rate**: ~5% of total messages
- **Events**: stream_start, stream_end, title_change, raid_incoming
- **Categories**: 20 popular game categories

## Troubleshooting

### Producer Issues

**Problem**: Can't connect to Kafka
```bash
# Solution: Verify Kafka is running
docker compose ps kafka
docker compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092
```

**Problem**: No messages in topics
```bash
# Solution: Check producer logs
docker compose logs twitch-producer

# Verify topics exist
kafka-topics --bootstrap-server localhost:9092 --list
```

### Spark Issues

**Problem**: Can't read from Kafka
```bash
# Solution: Verify Kafka connectivity
docker compose exec spark-streaming ping kafka

# Check topic has data
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat --max-messages 1
```

**Problem**: Can't write to PostgreSQL
```bash
# Solution: Verify PostgreSQL is running
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U telemetra -d telemetra
```

## Performance

### Resource Usage (Default Config)

| Component | CPU | Memory | Network |
|-----------|-----|--------|---------|
| Producer | ~5-10% | ~50-100MB | ~10-20 KB/sec |
| Kafka | ~10-20% | ~512MB | ~20-50 KB/sec |
| Spark | ~20-30% | ~1-2GB | ~20-50 KB/sec |

### Scaling

**Horizontal Scaling**:
```bash
# Scale producer
docker compose up -d --scale twitch-producer=3

# Add more Kafka brokers (update docker-compose.yml)
```

**Vertical Scaling**:
```bash
# Increase producer rate
docker compose run -e RATE_PER_SEC=100 twitch-producer

# Increase Spark resources (update docker-compose.yml)
```

## Testing

### Unit Tests
```bash
# Producer tests
cd producer
pytest test_producer.py  # (when available)

# Spark tests
cd spark
pytest test_spark_job.py
```

### Integration Tests
```bash
# End-to-end test
cd data_pipeline
make integration-test  # (when available)
```

### Manual Testing
```bash
# Test producer → Kafka
cd producer
python twitch_mock_producer.py &
sleep 5
python test_consumer.py telemetra.events.chat 10

# Test Kafka → Spark → Postgres
# (Start Spark job and check Postgres tables)
```

## Documentation

- **[Producer README](producer/README.md)** - Detailed producer docs
- **[Schema README](schemas/README.md)** - Schema specifications
- **[Spark README](spark/README.md)** - Spark job documentation
- **[QUICKSTART](QUICKSTART.md)** - Integration guide
- **[DELIVERY SUMMARY](../PRODUCER_DELIVERY_SUMMARY.md)** - Complete delivery docs

## File Structure

```
data_pipeline/
├── producer/                       # Mock data producer
│   ├── twitch_mock_producer.py    # Main producer (28KB)
│   ├── test_consumer.py           # Test utility (5.9KB)
│   ├── requirements.txt           # Python deps
│   ├── Dockerfile                 # Container image
│   ├── docker-compose.snippet.yml # Service definition
│   ├── Makefile                   # Build automation
│   ├── .env.example               # Config template
│   ├── README.md                  # Documentation
│   └── FILES_SUMMARY.md           # File listing
│
├── schemas/                        # JSON schemas
│   ├── chat_message.json          # Chat schema (2.6KB)
│   ├── viewer_count.json          # Viewer schema (1.8KB)
│   ├── transaction.json           # Transaction schema (2.8KB)
│   ├── stream_meta.json           # Metadata schema (2.9KB)
│   ├── validate_schema.py         # Validation tool
│   └── README.md                  # Schema docs
│
├── spark/                          # Spark streaming
│   ├── spark_streaming_job.py     # Main Spark job
│   ├── requirements.txt           # PySpark deps
│   ├── Dockerfile                 # Spark container
│   └── README.md                  # Documentation
│
├── README.md                       # This file
└── QUICKSTART.md                   # Integration guide
```

## Next Steps

1. **Integrate into MVP**:
   - Add to `infra/docker-compose.yml`
   - Configure backend to consume from Kafka
   - Set up Prometheus/Grafana monitoring

2. **Backend Integration**:
   - Kafka consumer for real-time data
   - WebSocket relay to frontend
   - Redis caching for latest metrics

3. **Frontend Integration**:
   - Connect to backend WebSocket
   - Display real-time charts (D3.js)
   - Show moments timeline

4. **Production Enhancements**:
   - Add Prometheus metrics
   - Implement Schema Registry
   - Set up distributed tracing
   - Configure log aggregation

## Contributing

When modifying the data pipeline:

1. Update schemas in `schemas/` first
2. Update producer to match new schemas
3. Update Spark job for new aggregations
4. Update documentation
5. Test end-to-end flow
6. Update integration guide

## License

Part of the Telemetra MVP project.

## Support

- **Issues**: Check troubleshooting sections in component READMEs
- **Documentation**: See `QUICKSTART.md` and component docs
- **Testing**: Use `test_consumer.py` and validation utilities
