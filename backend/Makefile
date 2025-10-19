# Makefile for Telemetra Backend

.PHONY: help install test lint format clean run docker-build docker-run

help:
	@echo "Telemetra Backend - Available Commands"
	@echo ""
	@echo "  make install        Install dependencies"
	@echo "  make test           Run tests"
	@echo "  make test-cov       Run tests with coverage"
	@echo "  make lint           Lint code"
	@echo "  make format         Format code"
	@echo "  make clean          Clean build artifacts"
	@echo "  make run            Run development server"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo ""

install:
	pip install -r requirements.txt
	pip install -r tests/requirements.txt

test:
	pytest

test-cov:
	pytest --cov=backend --cov-report=term-missing --cov-report=html

lint:
	flake8 backend/ --max-line-length=100 --exclude=__pycache__
	mypy backend/ --ignore-missing-imports

format:
	black backend/ tests/
	isort backend/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

run:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker build -t telemetra-backend .

docker-run:
	docker run -p 8000:8000 --env-file .env telemetra-backend
