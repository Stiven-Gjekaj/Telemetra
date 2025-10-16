# Telemetra MVP - Smoke Tests & Validation

This document provides comprehensive smoke tests and validation procedures for the Telemetra MVP.

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM available
- Ports 3000, 8000, 5432, 9092, 6379 available

## Quick Smoke Test (5 minutes)

```bash
# 1. Navigate to project directory
cd C:\Users\stive\Desktop\stuff\code\Telemetra

# 2. Set up environment
cp .env.example .env

# 3. Start services
docker compose -f infra/docker-compose.yml --profile dev up --build -d

# 4. Wait for services (takes ~2-3 minutes)
sleep 180

# 5. Run smoke tests
bash smoke_test.sh
```

## Detailed Validation Steps

### 1. Docker Compose Up

```bash
docker compose -f infra/docker-compose.yml --profile dev up --build -d
```

**Expected Output:**
- All services start without errors
- Container statuses show "healthy" or "running"

**Validation:**
```bash
docker compose -f infra/docker-compose.yml ps
```

### 2. Health Check - Backend API

```bash
curl http://localhost:8000/health
```

**Expected Output:**
```json
{"status":"ok"}
```

**Detailed Health Check:**
```bash
curl http://localhost:8000/api/v1/health
```

**Expected Output:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-16T...",
  "database": "ok",
  "redis": "ok"
}
```

### 3. Backend Logs - 10 Second Tail

```bash
docker compose -f infra/docker-compose.yml logs -f backend --tail=50 &
sleep 10
kill %1
```

**Expected Output:**
- INFO level logs showing successful startup
- No ERROR or CRITICAL messages
- Database connection established
- Redis connection established
- Server running on 0.0.0.0:8000

**Sample Expected Log:**
```
telemetra-backend | INFO:     Started server process
telemetra-backend | INFO:     Waiting for application startup.
telemetra-backend | INFO:     Connected to PostgreSQL
telemetra-backend | INFO:     Connected to Redis
telemetra-backend | INFO:     Application startup complete.
telemetra-backend | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4. Mock Producer - Kafka Messages

**Start producer and verify:**
```bash
# Run producer for 10 seconds
docker compose -f infra/docker-compose.yml logs -f producer --tail=50 &
producer_pid=$!
sleep 10
kill $producer_pid
```

**Expected Output:**
- Producer connecting to Kafka at kafka:9092
- Successfully sending messages
- Message count increasing
- Rate approximately matching RATE_PER_SEC env var (default: 10 msg/sec)

**Sample Expected Log:**
```
telemetra-producer | INFO - Successfully connected to Kafka at kafka:9092
telemetra-producer | INFO - Starting producer for channels: demo_stream
telemetra-producer | INFO - Target rate: 10 messages/second
telemetra-producer | INFO - Produced 100 messages (avg rate: 10.02 msgs/sec)
```

**Verify messages in Kafka:**
```bash
docker compose -f infra/docker-compose.yml exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic telemetra.events.chat \
  --from-beginning \
  --max-messages 5
```

**Expected Output:**
- 5 JSON messages with chat event data
- Each message contains: event_id, timestamp, stream_id, user_id, username, message, emotes

**Sample Message:**
```json
{
  "event_id": "chat_1234567890123_4567",
  "timestamp": "2025-10-16T10:30:45.123456+00:00",
  "stream_id": "demo_stream",
  "user_id": "user_42",
  "username": "user_42",
  "message": "Kappa Kappa",
  "emotes": ["Kappa"],
  "is_subscriber": true,
  "is_moderator": false,
  "badges": ["subscriber"]
}
```

### 5. Spark Streaming Job - Database Writes

**Check Spark job logs:**
```bash
docker compose -f infra/docker-compose.yml logs -f spark-streaming --tail=100 &
sleep 30
kill %1
```

**Expected Output:**
- Spark job started successfully
- Reading from Kafka topics: telemetra.events.chat, telemetra.events.viewer
- Processing batches
- Writing to PostgreSQL
- No exceptions or errors

**Sample Expected Log:**
```
telemetra-spark-streaming | INFO SparkContext: Running Spark version 3.5.0
telemetra-spark-streaming | INFO StreamingContext: Starting StreamingContext
telemetra-spark-streaming | INFO KafkaSource: Subscribed to topics: telemetra.events.chat, telemetra.events.viewer
telemetra-spark-streaming | INFO JDBCRelation: Writing batch to PostgreSQL
telemetra-spark-streaming | INFO StreamExecution: Batch 0 completed in 1234 ms
```

**Verify data in PostgreSQL:**
```bash
docker compose -f infra/docker-compose.yml exec postgres psql -U telemetra -d telemetra -c \
  "SELECT COUNT(*) FROM chat_summary_minute;"
```

**Expected Output:**
- Count > 0 (at least 1 row after 30 seconds)
- Confirms Spark is writing aggregates to database

**Sample Output:**
```
 count
-------
     3
(1 row)
```

**Check for moments (anomalies):**
```bash
docker compose -f infra/docker-compose.yml exec postgres psql -U telemetra -d telemetra -c \
  "SELECT COUNT(*) FROM moments;"
```

**Expected Output:**
- Count >= 0 (may be 0 if no anomalies detected yet)

### 6. WebSocket - Live Stream

**Using websocat (install first):**
```bash
# Install websocat: choco install websocat (Windows) or brew install websocat (Mac)

# Connect to WebSocket
websocat ws://localhost:8000/ws/live/demo_stream
```

**Expected Output:**
- Connection established
- JSON messages arriving every 1-2 seconds
- Messages contain: viewer_count, chat_rate, top_emotes, recent_moments

**Sample Message:**
```json
{
  "type": "metrics",
  "data": {
    "viewer_count": 1234,
    "chat_rate": 10.5,
    "avg_sentiment": 0.23,
    "top_emotes": [
      {"emote": "Kappa", "count": 45},
      {"emote": "PogChamp", "count": 32}
    ],
    "recent_moments": [
      {
        "id": "moment_123",
        "type": "chat_spike",
        "description": "Chat rate anomaly detected",
        "severity": "high",
        "timestamp": "2025-10-16T10:35:12+00:00"
      }
    ]
  },
  "timestamp": "2025-10-16T10:35:15+00:00"
}
```

**Alternative - Using curl (no install needed):**
```bash
curl -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
  http://localhost:8000/ws/live/demo_stream
```

### 7. Frontend Dashboard

**Access:**
```bash
# Open browser to:
http://localhost:3000
```

**Expected:**
- Dashboard loads without errors
- Shows "Connecting..." or "Connected" status
- PulseBar shows viewer count with animation
- ChatFlow shows line chart (may be empty initially)
- EmoteCloud shows word cloud or list
- MomentsTimeline shows detected anomalies (may be empty initially)

**Browser Console Check:**
- No JavaScript errors
- WebSocket connection established
- Messages being received

### 8. API Endpoints

**List streams:**
```bash
curl http://localhost:8000/api/v1/streams
```

**Expected:**
```json
{
  "streams": [
    {
      "stream_id": "demo_stream",
      "title": "Demo Stream",
      "created_at": "2025-10-16T10:00:00+00:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

**Get stream metrics:**
```bash
curl http://localhost:8000/api/v1/streams/demo_stream/metrics?limit=5
```

**Expected:**
- Array of metric objects
- Each with: window_start, window_end, chat_count, unique_chatters, avg_viewers, chat_rate, avg_sentiment, top_emotes

**Get moments:**
```bash
curl http://localhost:8000/api/v1/streams/demo_stream/moments?limit=5
```

**Expected:**
- Array of moment objects
- Each with: id, type, description, severity, timestamp, metadata

## Automated Smoke Test Script

Create `smoke_test.sh`:

```bash
#!/bin/bash

set -e

echo "=== Telemetra MVP Smoke Tests ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

# Helper function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3

    echo -n "Testing $name... "

    response=$(curl -s -w "\n%{http_code}" "$url" || echo "000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $http_code)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (Expected HTTP $expected, got $http_code)"
        echo "Response: $body"
        ((FAILED++))
        return 1
    fi
}

echo "1. Testing Backend Health..."
test_endpoint "Health Check" "http://localhost:8000/health" "200"

echo ""
echo "2. Testing Backend Detailed Health..."
test_endpoint "Detailed Health" "http://localhost:8000/api/v1/health" "200"

echo ""
echo "3. Testing API Endpoints..."
test_endpoint "List Streams" "http://localhost:8000/api/v1/streams" "200"
test_endpoint "Stream Metrics" "http://localhost:8000/api/v1/streams/demo_stream/metrics" "200"
test_endpoint "Stream Moments" "http://localhost:8000/api/v1/streams/demo_stream/moments" "200"

echo ""
echo "4. Testing Frontend..."
test_endpoint "Frontend Dashboard" "http://localhost:3000" "200"

echo ""
echo "5. Checking Service Status..."
running_services=$(docker compose -f infra/docker-compose.yml ps --services --filter "status=running" | wc -l)
echo "Running services: $running_services"
if [ "$running_services" -ge 10 ]; then
    echo -e "${GREEN}PASS${NC} (Expected >= 10, got $running_services)"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Expected >= 10, got $running_services)"
    ((FAILED++))
fi

echo ""
echo "6. Checking Database..."
echo -n "Checking PostgreSQL connection... "
if docker compose -f infra/docker-compose.yml exec -T postgres psql -U telemetra -d telemetra -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAILED++))
fi

echo -n "Checking chat_summary_minute table... "
count=$(docker compose -f infra/docker-compose.yml exec -T postgres psql -U telemetra -d telemetra -t -c "SELECT COUNT(*) FROM chat_summary_minute;" 2>/dev/null | tr -d ' \n' || echo "0")
if [ "$count" -gt 0 ] 2>/dev/null; then
    echo -e "${GREEN}PASS${NC} ($count rows)"
    ((PASSED++))
else
    echo -e "${YELLOW}WARN${NC} (No data yet, wait longer or check Spark job)"
fi

echo ""
echo "7. Checking Kafka..."
echo -n "Listing Kafka topics... "
topics=$(docker compose -f infra/docker-compose.yml exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null | grep telemetra | wc -l || echo "0")
if [ "$topics" -ge 4 ]; then
    echo -e "${GREEN}PASS${NC} ($topics topics)"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (Expected >= 4, got $topics)"
    ((FAILED++))
fi

echo ""
echo "=== Smoke Test Results ==="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Check logs above.${NC}"
    exit 1
fi
```

## Expected Results Summary

| Test | Expected Result | Time to Complete |
|------|----------------|------------------|
| Docker Compose Up | All services start | 2-3 minutes |
| Health Check | HTTP 200, `{"status":"ok"}` | Immediate |
| Backend Logs | INFO logs, no errors | 10 seconds |
| Producer | Messages sent to Kafka | 10 seconds |
| Kafka Consumer | 5 messages retrieved | Immediate |
| Spark Job | Data written to PostgreSQL | 30 seconds |
| PostgreSQL Count | Count > 0 | Immediate |
| WebSocket | JSON messages every 1-2s | Immediate |
| Frontend | Dashboard loads | Immediate |
| API Endpoints | All return HTTP 200 | Immediate |

**Total Validation Time: ~5 minutes**

## Troubleshooting

### No data in database after 30 seconds
- Check Spark job logs: `docker compose -f infra/docker-compose.yml logs spark-streaming`
- Verify Kafka messages: Use kafka-console-consumer
- Check producer logs: `docker compose -f infra/docker-compose.yml logs producer`

### Health check fails
- Verify PostgreSQL is running: `docker compose -f infra/docker-compose.yml ps postgres`
- Check backend logs: `docker compose -f infra/docker-compose.yml logs backend`
- Ensure .env file exists with correct values

### WebSocket not connecting
- Check backend is running: `curl http://localhost:8000/health`
- Verify CORS settings in backend/.env
- Check browser console for errors

### Frontend not loading
- Verify port 3000 is not in use: `netstat -an | find "3000"`
- Check frontend logs: `docker compose -f infra/docker-compose.yml logs frontend`
- Try rebuilding: `docker compose -f infra/docker-compose.yml build frontend`

## Cleanup

```bash
# Stop all services
docker compose -f infra/docker-compose.yml down

# Remove volumes (data will be lost)
docker compose -f infra/docker-compose.yml down -v

# Remove images
docker compose -f infra/docker-compose.yml down --rmi all
```
