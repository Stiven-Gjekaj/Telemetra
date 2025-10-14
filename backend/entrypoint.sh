#!/bin/bash
set -e

echo "Waiting for Postgres..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "postgres" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; do
  sleep 1
done
echo "Postgres is ready!"

echo "Waiting for Kafka..."
until curl -s kafka:29092 > /dev/null 2>&1 || [ $? -eq 52 ]; do
  sleep 1
done
echo "Kafka is ready!"

echo "Running database migrations..."
alembic upgrade head || echo "No migrations to run or migrations failed"

echo "Starting application..."
exec "$@"
