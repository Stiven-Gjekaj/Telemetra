# Twitch Mock Data Producer

A realistic Twitch streaming data generator for the Telemetra MVP project. Produces mock chat messages, viewer counts, transactions, and stream metadata to Kafka topics.

## Features

- **Realistic Data Generation**: Mimics actual Twitch streaming patterns
  - Chat messages with popular emotes (Kappa, PogChamp, LUL, etc.)
  - Dynamic viewer counts with realistic fluctuations
  - Transactions (donations, subscriptions, bits, gift subs)
  - Stream lifecycle events (start, stop, title changes, raids)

- **Configurable via Environment Variables**: Easy to customize for different scenarios
- **Production-Ready**: Proper error handling, logging, and graceful shutdown
- **Docker Support**: Runs seamlessly in containerized environments
- **High Performance**: Uses confluent-kafka-python for efficient message production

## Quick Start

### Running Locally

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (optional):
   ```bash
   export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   export CHANNELS=demo_stream,gaming_channel
   export RATE_PER_SEC=20
   ```

3. **Run the producer**:
   ```bash
   python twitch_mock_producer.py
   ```

### Running with Docker

1. **Build the image**:
   ```bash
   docker build -t telemetra-producer .
   ```

2. **Run the container**:
   ```bash
   docker run --rm \
     -e KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
     -e CHANNELS=demo_stream \
     -e RATE_PER_SEC=10 \
     telemetra-producer
   ```

## Configuration

All configuration is done via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker address(es) | `kafka:9092` |
| `CHANNELS` | Comma-separated list of channels | `demo_stream` |
| `RATE_PER_SEC` | Messages per second to produce | `10` |
| `MESSAGE_VARIANTS` | Number of message templates | `50` |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `PRODUCE_CHAT` | Enable chat message production | `true` |
| `PRODUCE_VIEWER` | Enable viewer count production | `true` |
| `PRODUCE_TRANSACTIONS` | Enable transaction production | `true` |
| `PRODUCE_STREAM_META` | Enable stream metadata production | `true` |

## Kafka Topics

The producer publishes to these topics:

### 1. `telemetra.events.chat`
Chat messages with emotes, sentiment indicators, and user metadata.

**Example**:
```json
{
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "channel": "demo_stream",
  "username": "gamer123",
  "user_id": "user_1234567",
  "message": "That was insane! PogChamp PogChamp",
  "emotes": ["PogChamp"],
  "badges": ["subscriber"],
  "is_action": false,
  "bits": 0,
  "sentiment_hint": "excited",
  "timestamp": "2025-10-16T10:30:00.123456Z",
  "metadata": {
    "client": "web",
    "color": "#FF5733"
  }
}
```

### 2. `telemetra.events.viewer`
Viewer count updates with additional metrics.

**Example**:
```json
{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "channel": "demo_stream",
  "viewer_count": 1234,
  "chatter_count": 123,
  "follower_count": 50000,
  "subscriber_count": 62,
  "timestamp": "2025-10-16T10:30:00.123456Z",
  "metadata": {
    "peak_today": 1500,
    "stream_uptime_seconds": 3600
  }
}
```

### 3. `telemetra.events.transactions`
Monetization events (donations, subscriptions, bits, gift subs).

**Example**:
```json
{
  "transaction_id": "txn_a1b2c3d4e5f6g7h8",
  "channel": "demo_stream",
  "username": "generous_viewer",
  "user_id": "user_7654321",
  "transaction_type": "donation",
  "amount": 50.00,
  "currency": "USD",
  "message": "Love the stream! Keep it up!",
  "is_anonymous": false,
  "timestamp": "2025-10-16T10:30:00.123456Z",
  "metadata": {
    "payment_method": "paypal",
    "refundable": true
  }
}
```

### 4. `telemetra.events.stream_meta`
Stream lifecycle and metadata changes.

**Example**:
```json
{
  "event_id": "123e4567-e89b-12d3-a456-426614174000",
  "channel": "demo_stream",
  "event_type": "stream_start",
  "timestamp": "2025-10-16T10:00:00.123456Z",
  "stream_id": "stream_1234567890",
  "title": "Chill vibes and good times",
  "category": "Just Chatting",
  "category_id": "cat_1234567",
  "language": "en",
  "is_mature": false,
  "tags": ["English", "Casual"],
  "metadata": {
    "stream_quality": "1080p60",
    "encoder": "NVENC"
  }
}
```

## Data Generation Patterns

### Chat Messages
- 70% of all messages
- Uses 50+ message templates with popular emotes
- Includes sentiment hints for downstream analysis
- Occasional messages with bits (3% chance)
- Realistic user badge distribution (subscribers, moderators, VIPs)

### Viewer Counts
- 20% of all messages
- Simulates realistic fluctuations using random walk
- Occasional spikes (raids, viral moments)
- Occasional drops (technical issues, boring segments)
- Chatter count is 5-20% of viewer count

### Transactions
- 5% of all messages
- Distribution:
  - 20% donations ($1-$500)
  - 30% subscriptions (Tier 1-3, Prime)
  - 25% bits (100-10,000)
  - 15% gift subs (1-100 subs)
  - 10% subscription renewals

### Stream Metadata
- 5% of all messages
- Events: stream start/stop, title changes, category changes, raids
- Includes stream quality, encoder info, tags

## Monitoring

The producer logs detailed information:

- Connection status and retries
- Messages produced per topic (every 100 messages)
- Actual production rate vs target
- Important events (transactions, raids, spikes)
- Delivery failures and errors

**Example log output**:
```
2025-10-16 10:30:00 - INFO - Configuration loaded: 1 channels, 10.0 msg/sec
2025-10-16 10:30:01 - INFO - Successfully connected to Kafka
2025-10-16 10:30:01 - INFO - All topics already exist
2025-10-16 10:30:01 - INFO - Stream started for channel: demo_stream
2025-10-16 10:30:01 - INFO - Starting message production...
2025-10-16 10:30:15 - INFO - Produced 100 messages | Actual rate: 10.2 msg/sec
2025-10-16 10:30:20 - INFO - Transaction: donation $50.00 from generous_viewer to demo_stream
2025-10-16 10:30:45 - INFO - Viewer spike: +250 viewers!
```

## Schemas

JSON schemas for all message types are available in `../schemas/`:
- `chat_message.json`
- `viewer_count.json`
- `transaction.json`
- `stream_meta.json`

These schemas can be used for validation, documentation, or Schema Registry integration.

## Troubleshooting

### Producer can't connect to Kafka
- Verify `KAFKA_BOOTSTRAP_SERVERS` is correct
- Ensure Kafka is running and accessible
- Check network connectivity
- Review firewall rules

### Messages not appearing in topics
- Use `kafka-console-consumer` to verify:
  ```bash
  kafka-console-consumer --bootstrap-server kafka:9092 \
    --topic telemetra.events.chat \
    --from-beginning
  ```
- Check producer logs for errors
- Verify topic creation with `kafka-topics --list`

### Low production rate
- Increase `RATE_PER_SEC` environment variable
- Check system resources (CPU, memory)
- Review Kafka broker performance

### High memory usage
- Reduce `RATE_PER_SEC`
- Reduce number of channels
- Check for message delivery failures (backpressure)

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests (when available)
pytest tests/ -v --cov=.
```

### Code Quality
```bash
# Format code
ruff format twitch_mock_producer.py

# Lint code
ruff check twitch_mock_producer.py

# Type checking
mypy twitch_mock_producer.py
```

## Performance Tuning

For high-throughput scenarios:

1. **Increase batch size**:
   - Modify `batch.size` in producer config (currently 16384 bytes)

2. **Adjust linger time**:
   - Increase `linger.ms` for better batching (currently 10ms)

3. **Use compression**:
   - Already enabled with `snappy` compression
   - Can switch to `lz4` or `zstd` for different trade-offs

4. **Run multiple instances**:
   - Use different `CHANNELS` for each instance
   - Distribute load across multiple containers

## License

Part of the Telemetra MVP project.
