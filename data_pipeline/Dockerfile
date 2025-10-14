FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    kafka-python==2.0.2

# Copy producer scripts
COPY producer/ ./producer/

# Default command (can be overridden)
CMD ["python", "/app/producer/twitch_mock_producer.py"]
