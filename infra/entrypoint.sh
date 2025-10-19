#!/bin/bash
# Telemetra Infrastructure Startup Script
# Ensures proper service initialization order

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "Telemetra MVP - Infrastructure Startup"
echo "========================================="
echo ""

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading .env configuration..."
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
else
    echo "ERROR: .env file not found!"
    echo "Please run: cp .env.example .env"
    exit 1
fi

# Configuration
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
PROFILE="${1:-dev}"
TIMEOUT="${2:-300}"

echo "Profile: $PROFILE"
echo "Timeout: ${TIMEOUT}s"
echo ""

# Check Docker
echo "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker-compose --version)"
echo ""

# Build images if needed
echo "Building Docker images..."
docker compose -f "$COMPOSE_FILE" build --pull 2>&1 | grep -E "(Building|built|CACHE|ERROR)" || true
echo ""

# Start services
echo "Starting services with profile: $PROFILE"
docker compose -f "$COMPOSE_FILE" --profile "$PROFILE" up -d

echo "Waiting for services to be healthy..."
echo ""

# Wait for critical services
declare -A services
services[zookeeper]="2181"
services[kafka]="9092"
services[postgres]="5432"
services[redis]="6379"

for service in "${!services[@]}"; do
    port="${services[$service]}"
    echo -n "Waiting for $service ($port)..."

    elapsed=0
    while ! nc -z localhost "$port" 2>/dev/null; do
        if [ $elapsed -ge $TIMEOUT ]; then
            echo " TIMEOUT"
            echo "ERROR: Service $service did not become ready after ${TIMEOUT}s"
            echo "Check logs: docker compose -f '$COMPOSE_FILE' logs $service"
            exit 1
        fi
        echo -n "."
        sleep 2
        elapsed=$((elapsed + 2))
    done
    echo " OK"
done

echo ""
echo "Waiting for application services..."

# Wait for backend health check
echo -n "Waiting for backend (/health)..."
elapsed=0
while ! curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    if [ $elapsed -ge $TIMEOUT ]; then
        echo " TIMEOUT"
        echo "ERROR: Backend health check did not pass after ${TIMEOUT}s"
        echo "Check logs: docker compose -f '$COMPOSE_FILE' logs backend"
        exit 1
    fi
    echo -n "."
    sleep 2
    elapsed=$((elapsed + 2))
done
echo " OK"

# Wait for frontend
echo -n "Waiting for frontend..."
elapsed=0
while ! wget -q --spider http://localhost:3000 2>/dev/null; do
    if [ $elapsed -ge $TIMEOUT ]; then
        echo " TIMEOUT"
        echo "WARNING: Frontend may not be fully ready"
        break
    fi
    echo -n "."
    sleep 2
    elapsed=$((elapsed + 2))
done
echo " OK"

echo ""
echo "========================================="
echo "Telemetra MVP Services Started Successfully!"
echo "========================================="
echo ""
echo "Access Points:"
echo "  Dashboard:  http://localhost:3000"
echo "  API Docs:   http://localhost:8000/docs"
echo "  API Health: http://localhost:8000/health"
echo "  Spark UI:   http://localhost:8080"
echo "  Kafka UI:   http://localhost:8888"
echo "  pgAdmin:    http://localhost:5050 (if using full profile)"
echo ""
echo "Quick Commands:"
echo "  View logs:     docker compose -f '$COMPOSE_FILE' logs -f"
echo "  Stop services: docker compose -f '$COMPOSE_FILE' down"
echo "  Health check:  curl http://localhost:8000/health"
echo ""
echo "Next Steps:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Check the dashboard for real-time metrics"
echo "  3. View logs with: make logs"
echo ""
