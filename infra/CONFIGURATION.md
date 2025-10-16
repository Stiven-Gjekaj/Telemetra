# Telemetra Infrastructure - Configuration Reference

Complete reference for all environment variables and configuration options.

## Environment Variables

### Database Configuration

#### POSTGRES_USER
- **Description**: PostgreSQL username for application
- **Type**: String
- **Default**: `telemetra`
- **Example**: `POSTGRES_USER=app_user`
- **Notes**: Used for database access throughout the stack

#### POSTGRES_PASSWORD
- **Description**: PostgreSQL password
- **Type**: String (plain text in .env)
- **Default**: `telemetra_dev_password`
- **Example**: `POSTGRES_PASSWORD=SecurePassword123`
- **Security Notes**:
  - NEVER commit .env to version control
  - Use strong passwords in production
  - Consider AWS Secrets Manager for prod

#### POSTGRES_DB
- **Description**: PostgreSQL database name
- **Type**: String
- **Default**: `telemetra`
- **Example**: `POSTGRES_DB=telemetra_prod`

#### POSTGRES_HOST
- **Description**: PostgreSQL hostname (internal or external)
- **Type**: String
- **Default**: `postgres` (Docker service name)
- **Example**: `POSTGRES_HOST=db.example.com`
- **Notes**: In Docker Compose, use service name; for external DB, use hostname/IP

#### POSTGRES_PORT
- **Description**: PostgreSQL connection port
- **Type**: Integer
- **Default**: `5432`
- **Example**: `POSTGRES_PORT=5432`

### Kafka Configuration

#### KAFKA_BOOTSTRAP_SERVERS
- **Description**: Kafka broker addresses for clients
- **Type**: CSV (comma-separated)
- **Default**: `kafka:29092` (Docker internal)
- **Examples**:
  - Internal: `kafka:29092`
  - External: `kafka1.example.com:9092,kafka2.example.com:9092`
  - Cloud: `pkc-xxx.region.provider.confluent.cloud:9092`
- **Notes**: Clients use this for producer/consumer connections

#### KAFKA_TOPIC_CHAT
- **Description**: Kafka topic for chat messages
- **Type**: String
- **Default**: `telemetra.events.chat`
- **Example**: `KAFKA_TOPIC_CHAT=chat_messages`
- **Notes**: Must match across producer and Spark job

#### KAFKA_TOPIC_VIEWER
- **Description**: Kafka topic for viewer count events
- **Type**: String
- **Default**: `telemetra.events.viewer`
- **Example**: `KAFKA_TOPIC_VIEWER=viewer_events`

#### KAFKA_TOPIC_TRANSACTIONS
- **Description**: Kafka topic for transaction events
- **Type**: String
- **Default**: `telemetra.events.transactions`
- **Example**: `KAFKA_TOPIC_TRANSACTIONS=payment_events`

#### KAFKA_TOPIC_STREAM_META
- **Description**: Kafka topic for stream metadata
- **Type**: String
- **Default**: `telemetra.events.stream_meta`
- **Example**: `KAFKA_TOPIC_STREAM_META=metadata`

#### KAFKA_LOG_RETENTION_HOURS
- **Description**: How long Kafka retains messages
- **Type**: Integer (hours)
- **Default**: `168` (7 days)
- **Examples**:
  - `24` = 1 day
  - `168` = 7 days
  - `720` = 30 days
- **Notes**: Older messages are automatically deleted

### Producer Configuration

#### PRODUCER_RATE_PER_SEC
- **Description**: Number of messages producer generates per second
- **Type**: Integer
- **Default**: `10`
- **Examples**:
  - `1` = Minimal test data
  - `10` = Normal development
  - `100` = Load testing
  - `1000` = Stress testing
- **Notes**: Affects CPU and memory usage

#### PRODUCER_CHANNELS
- **Description**: Comma-separated list of stream channels to simulate
- **Type**: CSV
- **Default**: `demo_stream`
- **Examples**:
  - Single: `demo_stream`
  - Multiple: `stream1,stream2,stream3`
- **Notes**: Creates one "stream" per entry

### Backend Configuration

#### REDIS_URL
- **Description**: Redis connection URL
- **Type**: URL
- **Default**: `redis://redis:6379`
- **Examples**:
  - Docker: `redis://redis:6379`
  - External: `redis://redis.example.com:6379`
  - With auth: `redis://:password@redis.example.com:6379`
- **Notes**: Used for caching latest metrics

#### API_TITLE
- **Description**: Title for API documentation
- **Type**: String
- **Default**: `Telemetra API`
- **Example**: `API_TITLE=Telemetra Streaming Analytics API`

#### CORS_ORIGINS
- **Description**: Allowed origins for CORS requests
- **Type**: CSV (comma-separated URLs)
- **Default**: `http://localhost:3000,http://localhost:5173`
- **Examples**:
  - Dev: `http://localhost:3000`
  - Prod: `https://telemetra.example.com`
  - Multiple: `https://app.example.com,https://api.example.com`
- **Security Notes**:
  - Be restrictive with CORS
  - Never use `*` in production
  - Only list actual frontend URLs

#### DEBUG
- **Description**: Enable debug mode (verbose logging)
- **Type**: Boolean
- **Default**: `false`
- **Values**: `true` or `false`
- **Notes**: Only use in development, impacts performance

### Frontend Configuration

#### VITE_API_URL
- **Description**: Backend API URL for frontend requests
- **Type**: URL (HTTP)
- **Default**: `http://localhost:8000`
- **Examples**:
  - Dev: `http://localhost:8000`
  - Prod: `https://api.telemetra.example.com`
- **Notes**: Used by React app for REST calls

#### VITE_WS_URL
- **Description**: Backend WebSocket URL for live metrics
- **Type**: URL (WebSocket)
- **Default**: `ws://localhost:8000`
- **Examples**:
  - Dev: `ws://localhost:8000`
  - Prod: `wss://api.telemetra.example.com`
- **Notes**: Use `wss://` for secure connections in production

### Logging Configuration

#### LOG_LEVEL
- **Description**: Application logging verbosity
- **Type**: String
- **Default**: `INFO`
- **Values**:
  - `DEBUG` = Most verbose (for debugging)
  - `INFO` = Normal operation
  - `WARNING` = Warnings and errors only
  - `ERROR` = Errors only
  - `CRITICAL` = Critical errors only
- **Performance Notes**: DEBUG level has performance overhead

### Admin Panel Configuration

#### PGADMIN_EMAIL
- **Description**: pgAdmin login email
- **Type**: String
- **Default**: `admin@telemetra.local`
- **Example**: `PGADMIN_EMAIL=admin@example.com`
- **Notes**: Used when accessing pgAdmin at port 5050

#### PGADMIN_PASSWORD
- **Description**: pgAdmin login password
- **Type**: String
- **Default**: `admin`
- **Example**: `PGADMIN_PASSWORD=SecurePassword123`
- **Security Notes**: Change for any non-local deployment

### Spark Configuration

#### SPARK_MASTER
- **Description**: Spark master URL
- **Type**: URL
- **Default**: `spark://spark-master:7077`
- **Examples**:
  - Local: `spark://spark-master:7077`
  - Remote: `spark://spark-master.example.com:7077`
  - Standalone: `local[*]`

#### SPARK_WORKER_MEMORY
- **Description**: Memory allocated per Spark worker
- **Type**: String with unit
- **Default**: `1G`
- **Examples**:
  - `512M` = 512 megabytes
  - `1G` = 1 gigabyte
  - `2G` = 2 gigabytes
- **Notes**: Total memory = WORKER_MEMORY × number of workers

#### SPARK_WORKER_CORES
- **Description**: CPU cores per Spark worker
- **Type**: Integer
- **Default**: `2`
- **Examples**:
  - `1` = Single core
  - `2` = Dual core
  - `4` = Quad core
- **Notes**: Affects parallelism within a worker

### Streaming Configuration

#### CHAT_WINDOW_DURATION_SECONDS
- **Description**: Size of aggregation window for chat metrics
- **Type**: Integer (seconds)
- **Default**: `60`
- **Examples**:
  - `30` = 30 second windows
  - `60` = 1 minute windows
  - `300` = 5 minute windows
- **Notes**: Larger windows = less granular but cheaper computation

#### CHAT_WINDOW_SLIDE_SECONDS
- **Description**: Slide interval for windowing (overlap)
- **Type**: Integer (seconds)
- **Default**: `10`
- **Example**: `CHAT_WINDOW_SLIDE_SECONDS=10`
- **Notes**: Smaller slides = more frequent aggregates, more computation

#### ANOMALY_DETECTION_THRESHOLD
- **Description**: Z-score threshold for anomaly detection
- **Type**: Float
- **Default**: `3.0`
- **Examples**:
  - `2.0` = Sensitive (more false positives)
  - `3.0` = Balanced
  - `4.0` = Conservative (fewer alerts)
- **Statistics**: 3σ catches ~99.7% of normal variation

#### CHAT_RETENTION_DAYS
- **Description**: Number of days to retain chat data
- **Type**: Integer
- **Default**: `7`
- **Examples**:
  - `1` = 1 day
  - `7` = 1 week
  - `30` = 1 month
- **Notes**: Older data is automatically deleted

## Configuration Examples

### Development (Default)
```bash
# Minimal, suitable for laptops
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=telemetra_dev_password
POSTGRES_DB=telemetra
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
PRODUCER_RATE_PER_SEC=10
LOG_LEVEL=INFO
DEBUG=false
```

### Load Testing
```bash
# Increased producer rate for testing system limits
PRODUCER_RATE_PER_SEC=100
CHAT_WINDOW_DURATION_SECONDS=30
CHAT_WINDOW_SLIDE_SECONDS=5
LOG_LEVEL=WARNING
DEBUG=false
```

### Production-like
```bash
# More realistic configuration
POSTGRES_PASSWORD=UseSecurePassword!
PRODUCER_RATE_PER_SEC=100
LOG_LEVEL=WARNING
DEBUG=false
CORS_ORIGINS=https://app.telemetra.example.com
VITE_API_URL=https://api.telemetra.example.com
VITE_WS_URL=wss://api.telemetra.example.com
```

### Debugging
```bash
# Maximum verbosity for troubleshooting
LOG_LEVEL=DEBUG
DEBUG=true
ANOMALY_DETECTION_THRESHOLD=2.0
```

## Configuration Validation

To validate your configuration:

```bash
# Check all required variables are set
grep -E "^[A-Z_]+=" .env

# Verify PostgreSQL connection
docker compose -f infra/docker-compose.yml exec postgres psql \
  -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1"

# Verify Kafka connectivity
docker compose -f infra/docker-compose.yml exec kafka \
  kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# Test Redis connection
docker compose -f infra/docker-compose.yml exec redis redis-cli ping
```

## Changing Configuration

### Dynamic Changes (no restart needed)
- `LOG_LEVEL` - Takes effect on next request
- `DEBUG` - Takes effect on restart of service
- `ANOMALY_DETECTION_THRESHOLD` - Takes effect on next aggregation

### Requires Service Restart
- Kafka settings (KAFKA_*)
- Producer settings (PRODUCER_*)
- Database location (POSTGRES_*)
- Redis location (REDIS_URL)

### Requires Full Stack Restart
- Network changes
- Major resource changes
- Spark configuration changes

To apply changes:

```bash
# 1. Update .env file
nano .env

# 2. For simple changes
docker compose -f infra/docker-compose.yml restart backend

# 3. For infrastructure changes
docker compose -f infra/docker-compose.yml down
docker compose -f infra/docker-compose.yml up -d
```

## Performance Tuning

### For Low Memory Machines (4GB)
```bash
SPARK_WORKER_MEMORY=512M
SPARK_WORKER_CORES=1
PRODUCER_RATE_PER_SEC=5
```

### For High-Throughput
```bash
PRODUCER_RATE_PER_SEC=1000
SPARK_WORKER_CORES=4
SPARK_WORKER_MEMORY=4G
CHAT_WINDOW_SLIDE_SECONDS=5
```

### For Real-Time Sensitivity
```bash
CHAT_WINDOW_DURATION_SECONDS=10
CHAT_WINDOW_SLIDE_SECONDS=2
ANOMALY_DETECTION_THRESHOLD=2.0
```

## Security Considerations

### Development
- Use default credentials only locally
- DEBUG can be true
- CORS can be permissive

### Production
- Strong passwords for POSTGRES_PASSWORD and PGADMIN_PASSWORD
- Restrict CORS_ORIGINS to actual domains
- DEBUG must be false
- Use TLS for all network connections (wss:// for WebSocket)
- Implement secret management (AWS Secrets Manager, HashiCorp Vault)
- Regular credential rotation

## Monitoring Configuration

To monitor actual values:

```bash
# View current environment in a container
docker compose -f infra/docker-compose.yml exec backend env | sort

# Check what the application loaded
docker compose -f infra/docker-compose.yml logs backend | grep -i "config\|loaded"
```

## Advanced: Override per Container

For specific use cases, override variables per service:

```yaml
# In docker-compose.yml for a specific service
environment:
  LOG_LEVEL: DEBUG  # Override for this service only
```

This is useful for running a debugging instance alongside normal operation.
