# Telemetra Spark Streaming Job - Files Summary

## Created Files Overview

This document provides a comprehensive overview of all files created for the Telemetra Spark streaming analytics pipeline.

---

## Core Application Files

### 1. `spark_streaming_job.py` (19,246 bytes)
**Purpose**: Main PySpark streaming application

**Key Features**:
- **Kafka Integration**: Reads from `telemetra.events.chat` and `telemetra.events.viewer` topics
- **Windowed Aggregations**:
  - 1-minute tumbling windows with 10-second slides
  - 10-second watermark for late data tolerance
- **Metrics Computed**:
  - `chat_count`: Total messages per window
  - `unique_chatters`: Distinct user count
  - `avg_sentiment`: Lexicon-based sentiment score
  - `top_emotes`: Most frequently used emotes (array)
  - `chat_rate`: Messages per second
  - `avg_viewers`: Average concurrent viewers
  - `positive_count` / `negative_count`: Sentiment distribution
- **Sentiment Analysis**:
  - Lexicon-based scoring with 20+ positive and negative words
  - Score range: -1.0 (negative) to +1.0 (positive)
- **Anomaly Detection**:
  - Z-score statistical method on chat_rate
  - Rolling window (last 10 time periods)
  - Configurable threshold (default: 3.0 standard deviations)
  - Detected anomalies written to `moments` table
- **PostgreSQL Output**:
  - JDBC batch writes to `chat_summary_minute` and `moments` tables
  - Fault-tolerant checkpointing
  - Error handling with logging

**Class Structure**:
```python
TelemetraStreamingJob
├── __init__()                      # Configuration from env vars
├── create_spark_session()          # Spark session setup
├── get_chat_schema()               # Chat event schema
├── get_viewer_schema()             # Viewer event schema
├── read_kafka_stream()             # Kafka source reader
├── compute_sentiment_score()       # Sentiment scoring
├── enrich_with_sentiment()         # Add sentiment to messages
├── aggregate_chat_metrics()        # Chat windowed aggregations
├── aggregate_viewer_metrics()      # Viewer windowed aggregations
├── join_metrics()                  # Combine chat + viewer streams
├── detect_anomalies()              # Z-score anomaly detection
├── prepare_summary_output()        # Format for DB write
├── prepare_moments_output()        # Extract anomalies
├── write_to_postgres()             # JDBC sink
└── run()                           # Main execution loop
```

---

## Docker & Deployment Files

### 2. `Dockerfile` (1,316 bytes)
**Purpose**: Container image definition

**Key Features**:
- **Base Image**: `apache/spark:3.5.0-python3`
- **Python Dependencies**: PySpark 3.5.0, py4j
- **System Tools**: curl, netcat for health checks
- **Checkpoint Directory**: `/tmp/spark-checkpoints` with proper permissions
- **Spark UI**: Exposed on port 4040
- **Health Check**: Monitors process with `pgrep`
- **Entrypoint**: Custom script with dependency waiting

**Build Command**:
```bash
docker build -t telemetra-spark-streaming:latest .
```

### 3. `entrypoint.sh` (3,242 bytes)
**Purpose**: Container startup script with dependency checks

**Key Features**:
- **Dependency Waiting**: Checks Kafka and PostgreSQL availability
- **Retry Logic**: 60 attempts with 2-second intervals
- **Configuration Display**: Shows Spark settings at startup
- **spark-submit Execution**: Launches job with optimal configuration
- **Graceful Shutdown**: Enables proper streaming query termination

**Packages Loaded**:
- `org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0`
- `org.postgresql:postgresql:42.7.1`

### 4. `docker-compose.spark.yml` (2,394 bytes)
**Purpose**: Standalone or integrated Docker Compose configuration

**Services**:
- **spark-streaming**: Main analytics job
- **spark-history** (optional): Spark History Server for past job analysis

**Volumes**:
- `spark-checkpoints`: Persistent checkpoint storage
- `spark-events`: Spark event logs

**Networking**: Uses `telemetra-network` (external)

**Resource Limits**:
- CPU: 2 cores (limit), 1 core (reservation)
- Memory: 4GB (limit), 2GB (reservation)

---

## Configuration Files

### 5. `requirements.txt` (395 bytes)
**Purpose**: Python dependencies

**Packages**:
- `pyspark==3.5.0`: Core Spark functionality
- `py4j==0.10.9.7`: Java-Python bridge

**Note**: Kafka and JDBC connectors loaded via `spark.jars.packages` at runtime

### 6. `config.example.env` (3,497 bytes)
**Purpose**: Environment variable template with documentation

**Configuration Categories**:
1. **Kafka Configuration**
   - Bootstrap servers
   - Multi-broker support
2. **PostgreSQL Configuration**
   - JDBC URL
   - Credentials
   - SSL options
3. **Spark Configuration**
   - Master URL (local, standalone, YARN, K8s)
   - Memory allocation
   - Executor cores
4. **Streaming Job Configuration**
   - Checkpoint location
   - Anomaly threshold
   - Window settings
5. **Performance Tuning**
   - Batch size limits
   - Trigger intervals
   - Watermark delays
6. **Security Settings**
   - Kafka SSL/SASL
   - PostgreSQL SSL
7. **Resource Limits**
   - Docker constraints

### 7. `.dockerignore` (287 bytes)
**Purpose**: Exclude unnecessary files from Docker build

**Excluded**:
- Python cache files (`__pycache__`, `*.pyc`)
- Virtual environments
- IDE files
- Git repository
- Test artifacts

---

## Documentation Files

### 8. `README.md` (11,522 bytes)
**Purpose**: Comprehensive technical documentation

**Sections**:
1. **Overview**: Architecture and features
2. **Architecture Diagram**: Kafka → Spark → PostgreSQL flow
3. **Features**: Detailed feature descriptions
4. **Configuration**: All environment variables
5. **Running the Job**: Three deployment options (Docker, local, cluster)
6. **Monitoring**: Spark UI, logs, metrics
7. **Development**: Local testing workflow
8. **Code Structure**: Module organization
9. **Troubleshooting**: Common issues and solutions
10. **Performance Tuning**: Throughput and latency optimization
11. **Production Considerations**: Security, monitoring, scaling

**Highlights**:
- Complete database schema definitions
- Sample SQL queries
- spark-submit examples
- Performance tuning guides

### 9. `INTEGRATION.md` (10,346 bytes)
**Purpose**: Integration guide for main Telemetra project

**Sections**:
1. **Integration Steps**: Complete Docker Compose integration
2. **Environment Variables**: Required configuration
3. **Database Schema**: SQL migration scripts
4. **Startup Sequence**: Service ordering with Makefile example
5. **Verification Steps**: Testing integration
6. **Monitoring Integration**: Prometheus and Grafana setup
7. **Development Workflow**: Hot-reload configuration
8. **Service Dependencies Graph**: Visual architecture
9. **Troubleshooting**: Integration-specific issues
10. **Performance Optimization**: Scaling guidelines

**Key Features**:
- Copy-paste Docker Compose snippets
- Complete SQL schema with partitioning
- Step-by-step verification commands
- Production deployment checklist

### 10. `QUICKSTART.md` (8,525 bytes)
**Purpose**: Get started in under 5 minutes

**Structure**:
1. **Prerequisites**: System requirements
2. **Quick Start (3 Steps)**:
   - Start infrastructure
   - Create database tables
   - Start Spark job
3. **Verification**: Logs and UI checks
4. **Testing the Pipeline**: Generate and verify data
5. **Common Commands**: Daily operations
6. **Troubleshooting**: Quick fixes
7. **Next Steps**: Tuning and scaling
8. **Architecture Overview**: Visual diagram
9. **Sample Queries**: Useful SQL examples

**Highlights**:
- Exact copy-paste commands
- Expected output examples
- Quick troubleshooting tips
- Practical SQL queries

---

## Testing & CI/CD Files

### 11. `test_spark_job.py` (9,817 bytes)
**Purpose**: Comprehensive unit test suite

**Test Classes**:
1. **TestSentimentScoring** (6 tests)
   - Positive, negative, neutral sentiment
   - Mixed sentiment
   - Empty message handling
   - Case-insensitivity
2. **TestSchemaDefinitions** (4 tests)
   - Chat schema structure and types
   - Viewer schema structure and types
3. **TestDataTransformations** (1 test)
   - Sentiment enrichment
4. **TestConfiguration** (3 tests)
   - Default values
   - Type checking
5. **TestSparkSession** (2 tests)
   - Session creation
   - Configuration validation
6. **TestLexicons** (4 tests)
   - Lexicon existence
   - No overlap
   - Format validation
7. **TestIntegration** (3 tests, marked)
   - Kafka connection (requires service)
   - PostgreSQL connection (requires service)
   - End-to-end processing (requires all services)

**Running Tests**:
```bash
pytest test_spark_job.py -v
pytest test_spark_job.py -v --cov=spark_streaming_job
```

### 12. `.github/workflows/spark-ci.yml`
**Purpose**: GitHub Actions CI/CD pipeline

**Jobs**:

**Job 1: lint-and-test** (15 min timeout)
- Python 3.12 setup
- Lint with ruff
- Type check with mypy
- Run pytest with coverage
- Upload coverage to Codecov

**Job 2: docker-build** (20 min timeout)
- Build Docker image
- Test image imports
- Cache layers with GitHub Actions cache

**Job 3: integration-test** (25 min timeout)
- **Services**: PostgreSQL, Zookeeper, Kafka
- **Steps**:
  1. Start infrastructure
  2. Create Kafka topics
  3. Set up database schema
  4. Produce test messages
  5. Run Spark job (90-second test)
  6. Verify data written to PostgreSQL
  7. Show sample results

**Triggers**:
- Push to main, develop, Rework branches
- Pull requests to main, develop
- Only when Spark files modified

---

## Development Tools

### 13. `Makefile` (4,188 bytes)
**Purpose**: Convenient development commands

**Targets**:

**Core Operations**:
- `make build`: Build Docker image
- `make run`: Start streaming job
- `make stop`: Stop job
- `make restart`: Restart job
- `make logs`: Tail logs
- `make clean`: Clean checkpoints and volumes

**Development**:
- `make shell`: Open container shell
- `make submit`: Local spark-submit
- `make test`: Run pytest
- `make install`: Install Python deps
- `make format`: Format with ruff
- `make lint`: Lint with ruff

**Monitoring**:
- `make ui`: Open Spark UI
- `make health`: Check service status
- `make stats`: Show resource usage

**Production**:
- `make deploy`: Production deployment (template)
- `make backup`: Backup checkpoints
- `make restore`: Restore checkpoints

**Usage**:
```bash
make help  # Show all commands
make build && make run
make logs
```

---

## File Organization

```
data_pipeline/spark/
├── Core Application
│   ├── spark_streaming_job.py      # Main application (19KB)
│   └── requirements.txt             # Dependencies (395B)
│
├── Docker & Deployment
│   ├── Dockerfile                   # Container definition (1.3KB)
│   ├── entrypoint.sh                # Startup script (3.2KB)
│   ├── docker-compose.spark.yml     # Compose config (2.4KB)
│   └── .dockerignore                # Build exclusions (287B)
│
├── Configuration
│   └── config.example.env           # Env var template (3.5KB)
│
├── Documentation
│   ├── README.md                    # Main documentation (11.5KB)
│   ├── INTEGRATION.md               # Integration guide (10.3KB)
│   ├── QUICKSTART.md                # Quick start guide (8.5KB)
│   └── FILES_SUMMARY.md             # This file
│
├── Testing
│   └── test_spark_job.py            # Unit tests (9.8KB)
│
└── Development Tools
    └── Makefile                     # Dev commands (4.2KB)

.github/workflows/
└── spark-ci.yml                     # CI/CD pipeline
```

**Total Files**: 14
**Total Size**: ~95KB

---

## Quick Reference Commands

### Build and Run
```bash
# Build image
docker build -t telemetra-spark-streaming:latest .

# Run with Docker Compose
docker compose -f docker-compose.spark.yml up -d

# View logs
docker logs -f telemetra-spark-streaming

# Access Spark UI
open http://localhost:4040
```

### Development
```bash
# Run tests
pytest test_spark_job.py -v

# Lint code
ruff check spark_streaming_job.py

# Format code
ruff format spark_streaming_job.py

# Local spark-submit
spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
  spark_streaming_job.py
```

### Verification
```bash
# Check data in PostgreSQL
docker exec -it telemetra-postgres psql -U telemetra -d telemetra -c \
  "SELECT COUNT(*) FROM chat_summary_minute;"

# Query recent anomalies
docker exec -it telemetra-postgres psql -U telemetra -d telemetra -c \
  "SELECT * FROM moments WHERE moment_type='chat_spike' ORDER BY detected_at DESC LIMIT 5;"
```

---

## Key Design Decisions

### 1. **Lexicon-Based Sentiment**
- **Why**: Simple, fast, no ML dependencies for MVP
- **Tradeoff**: Less accurate than ML models
- **Future**: Can be replaced with transformer models (BERT, RoBERTa)

### 2. **Z-Score Anomaly Detection**
- **Why**: Statistical method, no training required
- **Tradeoff**: Requires stable baseline, sensitive to distribution
- **Future**: Consider isolation forests or autoencoders

### 3. **1-Minute Windows with 10-Second Slides**
- **Why**: Balance between granularity and processing overhead
- **Tradeoff**: Not real-time, 60-second latency
- **Configurable**: Can adjust via `WINDOW_DURATION` and `SLIDE_DURATION`

### 4. **JDBC Batch Writes**
- **Why**: Simple, reliable, built-in backpressure
- **Tradeoff**: Not as performant as bulk COPY
- **Alternative**: Consider using PostgreSQL COPY for higher throughput

### 5. **Local Checkpoints**
- **Why**: Simple for development
- **Production**: Must use HDFS/S3 for fault tolerance
- **Configurable**: Via `CHECKPOINT_LOCATION` env var

### 6. **Flat Emote Array**
- **Why**: Simple querying, PostgreSQL array support
- **Tradeoff**: No frequency counts in array
- **Alternative**: Could use JSONB with counts

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker addresses |
| `POSTGRES_URL` | `jdbc:postgresql://postgres:5432/telemetra` | JDBC URL |
| `POSTGRES_USER` | `telemetra` | Database user |
| `POSTGRES_PASSWORD` | `telemetra` | Database password |
| `CHECKPOINT_LOCATION` | `/tmp/spark-checkpoints` | Checkpoint directory |
| `ANOMALY_THRESHOLD` | `3.0` | Z-score threshold |
| `SPARK_MASTER` | `local[*]` | Spark master URL |
| `SPARK_DRIVER_MEMORY` | `2g` | Driver memory |
| `SPARK_EXECUTOR_MEMORY` | `2g` | Executor memory |
| `SPARK_EXECUTOR_CORES` | `2` | Cores per executor |

---

## Production Readiness Checklist

- [x] Fault-tolerant checkpointing
- [x] Graceful shutdown handling
- [x] Health checks
- [x] Structured logging
- [x] Error handling with retries
- [x] Resource limits
- [x] Configuration via environment
- [x] Comprehensive documentation
- [x] Unit tests
- [x] Integration tests (CI)
- [ ] Monitoring metrics export (Prometheus)
- [ ] Distributed checkpoint storage (HDFS/S3)
- [ ] Alert configuration
- [ ] Load testing
- [ ] Disaster recovery procedures

---

## Next Steps for Production

1. **Metrics Export**: Add Prometheus metrics via custom listener
2. **Alert Rules**: Define alerts for processing delays, failures
3. **Checkpoint Backup**: Implement automated S3 backups
4. **Load Testing**: Test with production-scale data volumes
5. **ML Sentiment**: Replace lexicon with fine-tuned model
6. **Advanced Anomalies**: Add multiple anomaly types (viewer drops, emote spikes)
7. **Schema Registry**: Integrate Confluent Schema Registry for Avro
8. **Exactly-Once**: Enable idempotent writes with deduplication

---

## License

MIT License - See project LICENSE file for details

---

**Document Version**: 1.0
**Last Updated**: 2024-10-16
**Author**: Telemetra Team
