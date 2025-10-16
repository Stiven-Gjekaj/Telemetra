.PHONY: help setup up down restart logs clean build test health-check

help:
	@echo "Telemetra MVP - Make Commands"
	@echo "=============================="
	@echo ""
	@echo "Setup & Infrastructure:"
	@echo "  make setup           - Copy .env.example to .env (first time only)"
	@echo "  make build           - Build all Docker images"
	@echo "  make up              - Start all services (dev profile)"
	@echo "  make up-full         - Start all services including pgAdmin (full profile)"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo ""
	@echo "Monitoring & Debugging:"
	@echo "  make logs            - Tail logs from all services"
	@echo "  make logs-backend    - Tail backend service logs"
	@echo "  make logs-spark      - Tail spark streaming job logs"
	@echo "  make logs-kafka      - Tail Kafka logs"
	@echo "  make logs-producer   - Tail mock producer logs"
	@echo "  make ps              - Show running containers"
	@echo "  make health-check    - Health check all services"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run backend tests"
	@echo "  make test-integration - Run integration tests"
	@echo ""
	@echo "Cleaning:"
	@echo "  make clean           - Stop services and remove containers"
	@echo "  make clean-volumes   - Remove all volumes (data loss!)"
	@echo "  make clean-all       - Full cleanup including images"
	@echo ""
	@echo "Utilities:"
	@echo "  make kafka-topics    - List Kafka topics"
	@echo "  make kafka-consume   - Consume messages from telemetra.events.chat topic"
	@echo "  make db-shell        - Connect to PostgreSQL shell"
	@echo "  make redis-shell     - Connect to Redis shell"

setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env file created from .env.example"; \
	else \
		echo ".env file already exists"; \
	fi

build:
	docker compose -f infra/docker-compose.yml build --no-cache

up: setup
	docker compose -f infra/docker-compose.yml --profile dev up -d
	@echo ""
	@echo "Services are starting..."
	@echo "Frontend:  http://localhost:3000"
	@echo "API:       http://localhost:8000"
	@echo "Kafka UI:  http://localhost:8888"
	@echo "pgAdmin:   http://localhost:5050 (disabled in dev profile)"
	@echo "Spark UI:  http://localhost:8080"
	@echo ""
	@echo "Run 'make health-check' to verify all services are ready"

up-full: setup
	docker compose -f infra/docker-compose.yml --profile full --profile dev up -d
	@echo ""
	@echo "All services starting (including pgAdmin)..."
	@echo "Frontend:  http://localhost:3000"
	@echo "API:       http://localhost:8000"
	@echo "Kafka UI:  http://localhost:8888"
	@echo "pgAdmin:   http://localhost:5050"
	@echo "Spark UI:  http://localhost:8080"
	@echo ""
	@echo "Run 'make health-check' to verify all services are ready"

down:
	docker compose -f infra/docker-compose.yml down

restart: down up
	@echo "Services restarted"

logs:
	docker compose -f infra/docker-compose.yml logs -f

logs-backend:
	docker compose -f infra/docker-compose.yml logs -f backend

logs-spark:
	docker compose -f infra/docker-compose.yml logs -f spark-streaming-job

logs-kafka:
	docker compose -f infra/docker-compose.yml logs -f kafka

logs-producer:
	docker compose -f infra/docker-compose.yml logs -f mock-producer

ps:
	docker compose -f infra/docker-compose.yml ps -a

health-check:
	@echo "Checking service health..."
	@echo ""
	@docker compose -f infra/docker-compose.yml ps --services --filter "status=running" | while read service; do \
		echo -n "$$service: "; \
		docker compose -f infra/docker-compose.yml exec -T $$service sh -c 'exit 0' 2>/dev/null && echo "OK" || echo "NOT READY"; \
	done
	@echo ""
	@echo "Checking endpoints..."
	@echo -n "Backend /health: " && curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "Not available"
	@echo -n "Frontend: " && curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000 || echo "Not available"

test:
	docker compose -f infra/docker-compose.yml exec backend pytest /app/tests -v

test-integration:
	docker compose -f infra/docker-compose.yml exec backend pytest /app/tests/integration -v --timeout=30

clean:
	docker compose -f infra/docker-compose.yml down
	@echo "Containers stopped and removed"

clean-volumes:
	docker compose -f infra/docker-compose.yml down -v
	@echo "Containers and volumes removed"

clean-all: clean-volumes
	docker compose -f infra/docker-compose.yml down -v --remove-orphans --rmi all
	@echo "All containers, volumes, and images removed"

kafka-topics:
	docker compose -f infra/docker-compose.yml exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092

kafka-consume:
	docker compose -f infra/docker-compose.yml exec kafka kafka-console-consumer.sh \
		--bootstrap-server localhost:9092 \
		--topic telemetra.events.chat \
		--from-beginning \
		--max-messages 20

db-shell:
	docker compose -f infra/docker-compose.yml exec postgres psql -U $${POSTGRES_USER:-telemetra} -d $${POSTGRES_DB:-telemetra}

redis-shell:
	docker compose -f infra/docker-compose.yml exec redis redis-cli

.PHONY: help setup build up up-full down restart logs logs-backend logs-spark logs-kafka logs-producer ps health-check test test-integration clean clean-volumes clean-all kafka-topics kafka-consume db-shell redis-shell
