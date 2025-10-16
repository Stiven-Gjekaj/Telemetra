# Telemetra Monitoring Setup

This directory contains a minimal but functional Prometheus and Grafana monitoring setup for the Telemetra MVP project.

## Architecture

The monitoring stack consists of:

- **Prometheus** (port 9090): Metrics collection and storage
- **Grafana** (port 3001): Metrics visualization and dashboards
- **Redis Exporter** (port 9121): Exports Redis metrics
- **PostgreSQL Exporter** (port 9187): Exports PostgreSQL metrics
- **Kafka JMX Exporter** (port 9404): Exports Kafka JMX metrics

## Metrics Collection

### Backend FastAPI Metrics
- Endpoint: `http://backend:8000/metrics`
- Scrape interval: 15s
- Metrics include:
  - HTTP request duration (histograms for p50, p95, p99)
  - Request rate by method and endpoint
  - Error rates (4xx, 5xx)

### Kafka Metrics
- Endpoint: `http://kafka-jmx-exporter:9404/metrics`
- Scrape interval: 15s
- Metrics include:
  - Consumer lag by topic and partition
  - Broker metrics
  - Network request metrics

### Spark Metrics
- Endpoints:
  - Master: `http://spark-master:8080/metrics/prometheus`
  - Worker: `http://spark-worker:8081/metrics/prometheus`
- Scrape interval: 15s
- Metrics include:
  - Processing rate (records/sec)
  - Batch duration
  - Job execution metrics

### Redis Metrics
- Endpoint: `http://redis-exporter:9121/metrics`
- Scrape interval: 15s
- Metrics include:
  - Keyspace hits/misses (cache hit ratio)
  - Connected clients
  - Memory usage

### PostgreSQL Metrics
- Endpoint: `http://postgres-exporter:9187/metrics`
- Scrape interval: 15s
- Metrics include:
  - Active/idle connections
  - Transaction duration
  - Query performance

## Dashboard Panels

The Telemetra MVP Dashboard (`telemetra-mvp`) includes:

1. **API Latency**: p50, p95, p99 latencies for backend API requests
2. **Request Rate**: Requests per second by method and endpoint
3. **Error Rate**: 4xx and 5xx error rates as percentages
4. **Kafka Consumer Lag**: Current lag by topic and partition
5. **Spark Processing Rate**: Records processed per second
6. **Spark Batch Duration**: Time taken per batch
7. **Database Connection Pool**: Active, idle, and max transaction duration
8. **Redis Hit/Miss Ratio**: Cache effectiveness

## Getting Started

### 1. Start the monitoring stack

```bash
cd infra
docker-compose --profile dev up -d prometheus grafana redis-exporter postgres-exporter kafka-jmx-exporter
```

### 2. Access the services

- **Prometheus UI**: http://localhost:9090
- **Grafana**: http://localhost:3001
  - Default credentials: `admin / admin`
  - Dashboard will be automatically loaded

### 3. View metrics

The dashboard will be available immediately at:
http://localhost:3001/d/telemetra-mvp/telemetra-mvp-dashboard

## Configuration Files

### Prometheus Configuration
- **File**: `infra/prometheus.yml`
- **Purpose**: Defines scrape targets and intervals
- **Retention**: 7 days

### Grafana Datasource
- **File**: `infra/grafana/provisioning/datasources/prometheus.yml`
- **Purpose**: Automatically configures Prometheus as default datasource

### Grafana Dashboard Provisioning
- **File**: `infra/grafana/provisioning/dashboards/dashboard.yml`
- **Purpose**: Automatically loads dashboards from directory

### Telemetra Dashboard
- **File**: `infra/grafana/dashboards/telemetra-dashboard.json`
- **Purpose**: Pre-built dashboard with key metrics

### Kafka JMX Configuration
- **File**: `infra/jmx-exporter-config.yml`
- **Purpose**: Defines JMX metrics to export for Kafka

## Customization

### Adding New Metrics

1. Update your application to expose metrics at `/metrics` endpoint
2. Add scrape config to `prometheus.yml`:

```yaml
- job_name: 'my-service'
  static_configs:
    - targets: ['my-service:port']
  metrics_path: '/metrics'
  scrape_interval: 15s
```

3. Add panels to dashboard using Grafana UI

### Modifying Scrape Intervals

Edit `prometheus.yml` and change the `scrape_interval` for specific jobs or globally:

```yaml
global:
  scrape_interval: 30s  # Change global interval
```

### Adjusting Data Retention

Modify Prometheus retention in `docker-compose.yml`:

```yaml
command:
  - '--storage.tsdb.retention.time=14d'  # Change from 7d to 14d
```

## Troubleshooting

### Prometheus shows targets as "down"

1. Check if services are running:
```bash
docker-compose ps
```

2. Check Prometheus logs:
```bash
docker logs telemetra_prometheus
```

3. Verify network connectivity:
```bash
docker exec telemetra_prometheus wget -O- http://backend:8000/metrics
```

### Grafana dashboard is empty

1. Verify Prometheus datasource is configured:
   - Go to Configuration > Data Sources
   - Check Prometheus connection

2. Check if metrics are being collected:
   - Go to Prometheus UI: http://localhost:9090
   - Try query: `up{job="telemetra-backend"}`

3. Verify time range in Grafana matches data availability

### JMX Exporter not collecting Kafka metrics

1. Ensure Kafka container has JMX enabled
2. Check JMX exporter logs:
```bash
docker logs telemetra_kafka_jmx_exporter
```

## Resource Usage

The monitoring stack is configured with minimal resource limits for development:

- Prometheus: 256MB-512MB RAM, 0.25-0.5 CPU
- Grafana: 256MB-512MB RAM, 0.25-0.5 CPU
- Exporters: 64MB-128MB RAM each, 0.1-0.2 CPU

For production, increase these limits based on metrics volume and retention requirements.

## Production Considerations

For production deployment, consider:

1. **Persistent Storage**: Use external volumes for Prometheus and Grafana data
2. **Authentication**: Enable authentication for Prometheus and use strong passwords for Grafana
3. **Retention**: Adjust retention period based on compliance and capacity requirements
4. **High Availability**: Run multiple Prometheus instances with remote storage
5. **Alerting**: Configure Alertmanager for proactive monitoring
6. **HTTPS**: Enable TLS for all monitoring endpoints
7. **Access Control**: Implement RBAC in Grafana for multi-tenant access

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [PromQL Query Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)
