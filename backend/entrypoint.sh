#!/bin/bash
set -e

echo "Starting Telemetra Backend..."

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "PostgreSQL is up!"

# Wait for Kafka (optional, with timeout)
if [ -n "$KAFKA_BOOTSTRAP_SERVERS" ]; then
  echo "Waiting for Kafka..."
  KAFKA_HOST=$(echo $KAFKA_BOOTSTRAP_SERVERS | cut -d: -f1)
  KAFKA_PORT=$(echo $KAFKA_BOOTSTRAP_SERVERS | cut -d: -f2)

  timeout=60
  elapsed=0
  until nc -z $KAFKA_HOST $KAFKA_PORT 2>/dev/null || [ $elapsed -ge $timeout ]; do
    echo "Kafka is unavailable - sleeping"
    sleep 2
    elapsed=$((elapsed + 2))
  done

  if [ $elapsed -ge $timeout ]; then
    echo "Warning: Kafka connection timeout, continuing anyway..."
  else
    echo "Kafka is up!"
  fi
fi

# Wait for Redis (optional, with timeout)
if [ -n "$REDIS_HOST" ]; then
  echo "Waiting for Redis..."
  timeout=30
  elapsed=0
  until nc -z $REDIS_HOST $REDIS_PORT 2>/dev/null || [ $elapsed -ge $timeout ]; do
    echo "Redis is unavailable - sleeping"
    sleep 2
    elapsed=$((elapsed + 2))
  done

  if [ $elapsed -ge $timeout ]; then
    echo "Warning: Redis connection timeout, continuing anyway..."
  else
    echo "Redis is up!"
  fi
fi

echo "All dependencies are ready!"

# Execute the main command
exec "$@"
