# Makefile for Twitch Mock Producer

.PHONY: help install run test docker-build docker-run clean lint format

# Default target
help:
	@echo "Telemetra Twitch Mock Producer - Available commands:"
	@echo ""
	@echo "  make install       - Install Python dependencies"
	@echo "  make run           - Run the producer locally"
	@echo "  make test          - Run test consumer"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run producer in Docker"
	@echo "  make clean         - Clean up Python artifacts"
	@echo "  make lint          - Lint code with ruff"
	@echo "  make format        - Format code with ruff"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt
	pip install ruff mypy pytest  # Dev dependencies

# Run producer locally
run:
	@echo "Starting Twitch Mock Producer..."
	@export KAFKA_BOOTSTRAP_SERVERS=$${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092} && \
	export CHANNELS=$${CHANNELS:-demo_stream} && \
	export RATE_PER_SEC=$${RATE_PER_SEC:-10} && \
	python twitch_mock_producer.py

# Run test consumer
test:
	@echo "Starting test consumer..."
	@export KAFKA_BOOTSTRAP_SERVERS=$${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092} && \
	python test_consumer.py

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t telemetra-producer:latest .

# Run in Docker (standalone)
docker-run: docker-build
	@echo "Running producer in Docker..."
	docker run --rm \
		--name telemetra-producer \
		--network host \
		-e KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
		-e CHANNELS=demo_stream \
		-e RATE_PER_SEC=10 \
		-e LOG_LEVEL=INFO \
		telemetra-producer:latest

# Clean Python artifacts
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

# Lint code
lint:
	@echo "Linting code with ruff..."
	ruff check twitch_mock_producer.py test_consumer.py

# Format code
format:
	@echo "Formatting code with ruff..."
	ruff format twitch_mock_producer.py test_consumer.py

# Type checking
typecheck:
	@echo "Type checking with mypy..."
	mypy twitch_mock_producer.py

# Run all quality checks
quality: format lint typecheck
	@echo "All quality checks passed!"

# Quick local test (produce 100 messages)
quick-test:
	@echo "Running quick test (100 messages)..."
	@export KAFKA_BOOTSTRAP_SERVERS=localhost:9092 && \
	export CHANNELS=test_channel && \
	export RATE_PER_SEC=50 && \
	timeout 2 python twitch_mock_producer.py || true
	@echo "Producer test completed. Check Kafka topics."
