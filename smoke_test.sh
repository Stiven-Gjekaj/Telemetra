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

    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo -e "\n000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" = "$expected" ]; then
        echo -e "${GREEN}PASS${NC} (HTTP $http_code)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}FAIL${NC} (Expected HTTP $expected, got $http_code)"
        if [ ! -z "$body" ]; then
            echo "Response: $body"
        fi
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
cd "$(dirname "$0")"
running_services=$(docker compose -f infra/docker-compose.yml ps --services --filter "status=running" 2>/dev/null | wc -l)
echo "Running services: $running_services"
if [ "$running_services" -ge 8 ]; then
    echo -e "${GREEN}PASS${NC} (Expected >= 8, got $running_services)"
    ((PASSED++))
else
    echo -e "${YELLOW}WARN${NC} (Expected >= 8, got $running_services)"
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

echo -n "Checking database tables exist... "
tables=$(docker compose -f infra/docker-compose.yml exec -T postgres psql -U telemetra -d telemetra -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' \n' || echo "0")
if [ "$tables" -gt 0 ] 2>/dev/null; then
    echo -e "${GREEN}PASS${NC} ($tables tables)"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC} (No tables found)"
    ((FAILED++))
fi

echo ""
echo "7. Checking Kafka..."
echo -n "Listing Kafka topics... "
topics=$(docker compose -f infra/docker-compose.yml exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null | grep -c telemetra || echo "0")
if [ "$topics" -ge 4 ]; then
    echo -e "${GREEN}PASS${NC} ($topics topics)"
    ((PASSED++))
elif [ "$topics" -gt 0 ]; then
    echo -e "${YELLOW}WARN${NC} (Expected 4, got $topics)"
else
    echo -e "${RED}FAIL${NC} (No topics found)"
    ((FAILED++))
fi

echo ""
echo "8. Checking Redis..."
echo -n "Testing Redis connection... "
if docker compose -f infra/docker-compose.yml exec -T redis redis-cli PING 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAILED++))
fi

echo ""
echo "=== Smoke Test Results ==="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Check logs above.${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "  - Wait 2-3 minutes after 'docker compose up' for all services to start"
    echo "  - Check logs: docker compose -f infra/docker-compose.yml logs"
    echo "  - Verify .env file exists: cp .env.example .env"
    exit 1
fi
