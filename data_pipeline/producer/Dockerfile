# Multi-stage build for optimized Python 3.12 producer
FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# Final stage - minimal runtime image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    librdkafka1 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY twitch_mock_producer.py .

# Copy schemas for reference (optional)
COPY ../schemas /app/schemas

# Create non-root user for security
RUN useradd -m -u 1000 producer && \
    chown -R producer:producer /app

USER producer

# Health check (producer is fire-and-forget, so this just checks if process is alive)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f twitch_mock_producer.py || exit 1

# Default configuration via environment variables
ENV KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
    CHANNELS=demo_stream \
    RATE_PER_SEC=10 \
    MESSAGE_VARIANTS=50 \
    LOG_LEVEL=INFO

# Run the producer
CMD ["python", "twitch_mock_producer.py"]
