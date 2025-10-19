#!/bin/bash
set -e

# Telemetra Spark Streaming Job Entrypoint
# Handles service dependencies and spark-submit execution

echo "========================================"
echo "Telemetra Spark Streaming Job"
echo "========================================"

# Configuration
KAFKA_HOST="${KAFKA_BOOTSTRAP_SERVERS%%:*}"
KAFKA_PORT="${KAFKA_BOOTSTRAP_SERVERS##*:}"
POSTGRES_HOST=$(echo "$POSTGRES_URL" | sed -n 's|.*://\([^:]*\):.*|\1|p')
POSTGRES_PORT=$(echo "$POSTGRES_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')

# Default values
KAFKA_HOST=${KAFKA_HOST:-kafka}
KAFKA_PORT=${KAFKA_PORT:-9092}
POSTGRES_HOST=${POSTGRES_HOST:-postgres}
POSTGRES_PORT=${POSTGRES_PORT:-5432}

echo "Waiting for dependencies..."
echo "- Kafka: $KAFKA_HOST:$KAFKA_PORT"
echo "- PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT"

# Wait for Kafka
echo "Checking Kafka connectivity..."
MAX_RETRIES=60
RETRY_COUNT=0

while ! nc -z "$KAFKA_HOST" "$KAFKA_PORT" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: Kafka not available after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "Waiting for Kafka... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✓ Kafka is available"

# Wait for PostgreSQL
echo "Checking PostgreSQL connectivity..."
RETRY_COUNT=0

while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "ERROR: PostgreSQL not available after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "Waiting for PostgreSQL... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✓ PostgreSQL is available"

# Additional wait to ensure services are fully ready
echo "Waiting 10 seconds for services to stabilize..."
sleep 10

echo "========================================"
echo "Starting Spark Streaming Job"
echo "========================================"

# Spark configuration
SPARK_MASTER="${SPARK_MASTER:-local[*]}"
DRIVER_MEMORY="${SPARK_DRIVER_MEMORY:-2g}"
EXECUTOR_MEMORY="${SPARK_EXECUTOR_MEMORY:-2g}"
EXECUTOR_CORES="${SPARK_EXECUTOR_CORES:-2}"

echo "Spark Configuration:"
echo "- Master: $SPARK_MASTER"
echo "- Driver Memory: $DRIVER_MEMORY"
echo "- Executor Memory: $EXECUTOR_MEMORY"
echo "- Executor Cores: $EXECUTOR_CORES"
echo "========================================"

# Execute spark-submit with proper configuration
exec spark-submit \
    --master "$SPARK_MASTER" \
    --deploy-mode client \
    --driver-memory "$DRIVER_MEMORY" \
    --executor-memory "$EXECUTOR_MEMORY" \
    --executor-cores "$EXECUTOR_CORES" \
    --conf spark.streaming.stopGracefullyOnShutdown=true \
    --conf spark.sql.streaming.checkpointLocation="$CHECKPOINT_LOCATION" \
    --conf spark.sql.adaptive.enabled=true \
    --conf spark.sql.adaptive.coalescePartitions.enabled=true \
    --conf spark.ui.enabled=true \
    --conf spark.ui.port=4040 \
    --conf spark.eventLog.enabled=true \
    --conf spark.eventLog.dir=/tmp/spark-events \
    --conf spark.sql.streaming.metricsEnabled=true \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
    --py-files /app/spark_streaming_job.py \
    /app/spark_streaming_job.py
