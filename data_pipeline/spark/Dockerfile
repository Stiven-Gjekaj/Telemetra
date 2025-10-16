# Telemetra Spark Streaming Job Dockerfile
# Multi-stage build for optimized image size

FROM apache/spark:3.5.0-python3 AS base

# Switch to root for package installation
USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY spark_streaming_job.py .
COPY entrypoint.sh .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Create checkpoint directory with proper permissions
RUN mkdir -p /tmp/spark-checkpoints && \
    chmod 777 /tmp/spark-checkpoints

# Create directory for Spark event logs
RUN mkdir -p /tmp/spark-events && \
    chmod 777 /tmp/spark-events

# Switch back to spark user for runtime
USER spark

# Set environment variables
ENV SPARK_HOME=/opt/spark
ENV PATH="${SPARK_HOME}/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

# Expose Spark UI port
EXPOSE 4040

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -f spark_streaming_job || exit 1

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
