# Telemetra Spark Streaming Job Makefile
# Provides convenient commands for building, running, and managing the Spark job

.PHONY: help build run stop logs clean test deploy

# Default target
help:
	@echo "Telemetra Spark Streaming Job - Available Commands:"
	@echo ""
	@echo "  make build          - Build Docker image"
	@echo "  make run            - Start Spark streaming job"
	@echo "  make stop           - Stop Spark streaming job"
	@echo "  make restart        - Restart Spark streaming job"
	@echo "  make logs           - Tail streaming job logs"
	@echo "  make ui             - Open Spark UI in browser"
	@echo "  make test           - Run local tests"
	@echo "  make clean          - Clean checkpoints and logs"
	@echo "  make shell          - Open shell in Spark container"
	@echo "  make submit         - Submit job via spark-submit (local)"
	@echo "  make deploy         - Deploy to production cluster"
	@echo ""

# Build Docker image
build:
	@echo "Building Spark streaming job Docker image..."
	docker build -t telemetra-spark-streaming:latest .

# Run with Docker Compose
run:
	@echo "Starting Spark streaming job..."
	docker compose -f docker-compose.spark.yml up -d spark-streaming

# Stop service
stop:
	@echo "Stopping Spark streaming job..."
	docker compose -f docker-compose.spark.yml stop spark-streaming

# Restart service
restart: stop run

# View logs
logs:
	@echo "Tailing Spark streaming job logs (Ctrl+C to exit)..."
	docker compose -f docker-compose.spark.yml logs -f spark-streaming

# Open Spark UI
ui:
	@echo "Opening Spark UI at http://localhost:4040"
	@command -v xdg-open >/dev/null && xdg-open http://localhost:4040 || \
	 command -v open >/dev/null && open http://localhost:4040 || \
	 echo "Please open http://localhost:4040 in your browser"

# Run local tests
test:
	@echo "Running unit tests..."
	pytest tests/ -v

# Clean checkpoints and temporary data
clean:
	@echo "Cleaning checkpoints and temporary files..."
	docker compose -f docker-compose.spark.yml down -v
	rm -rf /tmp/spark-checkpoints/*
	rm -rf /tmp/spark-events/*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Open shell in container
shell:
	@echo "Opening shell in Spark container..."
	docker exec -it telemetra-spark-streaming bash

# Local spark-submit
submit:
	@echo "Submitting job locally with spark-submit..."
	spark-submit \
	  --master local[*] \
	  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.1 \
	  --driver-memory 2g \
	  spark_streaming_job.py

# Deploy to production (customize for your infrastructure)
deploy:
	@echo "Deploying to production cluster..."
	@echo "⚠️  Please customize this target for your production environment"
	@echo "Example for Kubernetes:"
	@echo "  kubectl apply -f k8s/spark-streaming-deployment.yaml"
	@echo "Example for Spark cluster:"
	@echo "  spark-submit --master spark://master:7077 --deploy-mode cluster ..."

# Development: Install Python dependencies locally
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt

# Development: Format code
format:
	@echo "Formatting code with ruff..."
	ruff format spark_streaming_job.py

# Development: Lint code
lint:
	@echo "Linting code with ruff..."
	ruff check spark_streaming_job.py

# Check service health
health:
	@echo "Checking Spark streaming job health..."
	@docker ps --filter "name=telemetra-spark-streaming" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Show resource usage
stats:
	@echo "Resource usage for Spark streaming job:"
	@docker stats telemetra-spark-streaming --no-stream

# Backup checkpoints
backup:
	@echo "Backing up checkpoints..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	docker cp telemetra-spark-streaming:/tmp/spark-checkpoints ./backups/checkpoints_$$timestamp
	@echo "Checkpoint backup completed"

# Restore checkpoints from backup
restore:
	@echo "Available backups:"
	@ls -la ./backups/
	@echo ""
	@read -p "Enter backup directory name to restore: " backup; \
	docker cp ./backups/$$backup/. telemetra-spark-streaming:/tmp/spark-checkpoints/
	@echo "Checkpoint restore completed"
