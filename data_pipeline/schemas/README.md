# Telemetra Event Schemas

JSON Schema definitions for all Kafka message types in the Telemetra platform.

## Schema Files

### 1. `chat_message.json`
Chat messages from viewers with emotes, sentiment, and metadata.

**Required Fields**: `message_id`, `channel`, `username`, `message`, `timestamp`

**Key Features**:
- Emote detection and tracking
- User badges (subscriber, moderator, VIP, etc.)
- Sentiment hints for downstream analysis
- Bits/cheering support
- Action messages (`/me` commands)

### 2. `viewer_count.json`
Viewer count and engagement metrics.

**Required Fields**: `event_id`, `channel`, `viewer_count`, `timestamp`

**Key Features**:
- Current viewer count
- Active chatter count
- Follower and subscriber counts
- Peak viewer tracking
- Stream uptime

### 3. `transaction.json`
Monetization events including donations, subscriptions, and bits.

**Required Fields**: `transaction_id`, `channel`, `transaction_type`, `amount`, `timestamp`

**Supported Transaction Types**:
- `donation`: Direct monetary donations
- `subscription`: Monthly subscriptions (Tier 1-3, Prime)
- `bits`: Twitch bits/cheering
- `gift_sub`: Gift subscriptions to other users
- `subscription_renewal`: Recurring subscription payments

### 4. `stream_meta.json`
Stream lifecycle and metadata events.

**Required Fields**: `event_id`, `channel`, `event_type`, `timestamp`

**Supported Event Types**:
- `stream_start`: Stream goes live
- `stream_end`: Stream ends
- `title_change`: Stream title updated
- `category_change`: Game/category changed
- `raid_incoming`: Receiving raid from another channel
- `raid_outgoing`: Raiding another channel
- `host_start`: Starting to host another channel
- `host_end`: Stopping host

## Usage

### Validation with Python

Use the included `validate_schema.py` utility:

```bash
# Validate a chat message
python validate_schema.py chat_message.json '{"message_id": "test-123", ...}'

# Validate from file
python validate_schema.py viewer_count.json "$(cat sample_viewer.json)"
```

### Validation with online tools

1. Copy schema content from any `.json` file
2. Visit https://www.jsonschemavalidator.net/
3. Paste schema in left panel
4. Paste message JSON in right panel
5. See validation results

### Integration with Schema Registry

These schemas can be registered with Confluent Schema Registry:

```bash
# Register chat message schema
curl -X POST http://localhost:8081/subjects/telemetra.events.chat-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  --data @chat_message.json

# List all schemas
curl http://localhost:8081/subjects
```

## Schema Versioning

Schemas follow semantic versioning:
- **Major version**: Breaking changes (field removal, type changes)
- **Minor version**: Backward-compatible additions (new optional fields)
- **Patch version**: Non-functional changes (descriptions, examples)

Current version: **1.0.0** (initial release)

## Best Practices

### When Producing Messages

1. **Always include required fields**: Validate before sending to Kafka
2. **Use proper data types**: Strings for IDs, integers for counts, etc.
3. **Include timestamps in ISO 8601 format**: `YYYY-MM-DDTHH:MM:SS.ffffffZ`
4. **Generate unique IDs**: Use UUID v4 for message/event IDs
5. **Keep messages under 1MB**: Kafka default max message size

### When Consuming Messages

1. **Handle schema evolution**: Support both old and new schema versions
2. **Validate optional fields**: Check existence before accessing
3. **Parse timestamps properly**: Use ISO 8601 parsers
4. **Handle unknown fields**: Ignore fields not in your version
5. **Log validation errors**: Don't silently drop invalid messages

## Example Messages

### Chat Message
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

### Viewer Count
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

### Transaction
```json
{
  "transaction_id": "txn_a1b2c3d4e5f6g7h8",
  "channel": "demo_stream",
  "username": "generous_viewer",
  "user_id": "user_7654321",
  "transaction_type": "donation",
  "amount": 50.00,
  "currency": "USD",
  "message": "Love the stream!",
  "is_anonymous": false,
  "timestamp": "2025-10-16T10:30:00.123456Z",
  "metadata": {
    "payment_method": "paypal",
    "refundable": true
  }
}
```

### Stream Metadata
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

## Schema Evolution Guidelines

### Adding a New Field
1. Make it optional with a default value
2. Document in schema description
3. Update example messages
4. Increment minor version

### Removing a Field
1. Deprecate first (mark in description)
2. Wait for all consumers to upgrade
3. Remove in next major version
4. Update all examples

### Changing Field Type
1. Create new field with new name
2. Populate both fields during transition
3. Deprecate old field
4. Remove old field in next major version

## Contributing

When modifying schemas:

1. Update the schema file
2. Update this README with examples
3. Update the `validate_schema.py` tests
4. Update producer code to match
5. Version appropriately
6. Document in changelog

## Resources

- [JSON Schema Specification](https://json-schema.org/)
- [Understanding JSON Schema](https://json-schema.org/understanding-json-schema/)
- [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)
- [Schema Evolution Best Practices](https://docs.confluent.io/platform/current/schema-registry/avro.html#schema-evolution)
