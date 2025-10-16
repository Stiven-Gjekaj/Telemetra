# Telemetra CI/CD Workflow Documentation

## Overview

The GitHub Actions CI/CD workflow (`ci.yml`) provides comprehensive automated testing for the Telemetra MVP project. It orchestrates a full Docker Compose stack, runs backend tests, and performs smoke tests against the API endpoints.

## Workflow Triggers

The workflow is triggered on:

- **Push to main branch**: Runs on every push to the main branch
- **Pull requests to main branch**: Runs on every PR to main

```yaml
on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
```

## Workflow Jobs

### Job 1: CI - Test Backend with Docker Compose

**Purpose**: Main testing job that orchestrates the entire test stack

**Runner**: `ubuntu-latest`
**Timeout**: 30 minutes

#### Step-by-Step Breakdown

##### 1. Checkout Code
```yaml
- name: Checkout code
  uses: actions/checkout@v4
```
- Clones the repository code
- Sets fetch depth to 0 for full history access

##### 2. Set up Docker Buildx
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3
```
- Enables advanced Docker image building capabilities
- Supports building images for different architectures

##### 3. Copy Environment Configuration
```yaml
- name: Copy environment configuration
  run: cp .env.example .env
```
- Copies `.env.example` to `.env` for Docker Compose
- Docker Compose reads this file for environment variables
- Ensures consistent configuration across CI runs

##### 4. Pull Base Images
```yaml
- name: Pull base images
  run: |
    docker pull confluentinc/cp-zookeeper:7.5.0 || true
    docker pull confluentinc/cp-kafka:7.5.0 || true
    docker pull postgres:15-alpine || true
    docker pull redis:7-alpine || true
    docker pull bitnami/spark:3.5.0 || true
```
- Pre-pulls base Docker images to speed up service startup
- Uses `|| true` to continue even if pulls fail (images might already exist)
- Reduces overall pipeline execution time

##### 5. Start Docker Compose Services
```yaml
- name: Start services with Docker Compose
  run: |
    docker compose -f infra/docker-compose.yml --profile dev up -d
    sleep 5
```
- Starts all services in the "dev" profile:
  - PostgreSQL database
  - Redis cache
  - Kafka message broker (with Zookeeper)
  - Spark Master and Worker nodes
  - Mock Producer
  - Spark Streaming Job
  - Backend API
  - Frontend (optional)
- Uses `-d` flag for detached mode (background execution)
- Waits 5 seconds for services to initialize

**Services Started**:
- **PostgreSQL 15**: Primary database for stream aggregates and moments
- **Redis 7**: Cache layer for metrics and data
- **Kafka 7.5**: Message broker for event streaming
- **Zookeeper 7.5**: Coordination for Kafka cluster
- **Spark 3.5**: Distributed computing for stream aggregations
- **Backend FastAPI**: REST API and WebSocket server
- **Mock Producer**: Generates test stream data
- **Spark Streaming Job**: Processes Kafka events

##### 6. Verify Docker Compose Status
```yaml
- name: Verify Docker Compose status
  run: |
    docker compose -f infra/docker-compose.yml ps
    docker compose -f infra/docker-compose.yml logs --tail=20
```
- Displays running containers and their status
- Shows last 20 log lines from all services for debugging

##### 7. Wait for Backend Health Check
```yaml
- name: Wait for backend health check
  run: |
    max_attempts=10
    attempt=1
    delay=10

    while [ $attempt -le $max_attempts ]; do
      if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "Health check passed!"
        exit 0
      fi

      if [ $attempt -lt $max_attempts ]; then
        sleep $delay
      fi

      attempt=$((attempt + 1))
    done
```
- **Polling Logic**: Retries up to 10 times with 10-second delays (100 seconds total)
- **Endpoint**: `GET http://localhost:8000/health`
- **Success Criteria**: HTTP 200 response from health endpoint
- **Failure Handling**: Displays all Docker Compose logs if health check fails

##### 8. Verify Database Connectivity
```yaml
- name: Verify database connectivity
  run: |
    docker compose -f infra/docker-compose.yml exec -T postgres pg_isready -U telemetra -d telemetra
```
- Tests PostgreSQL readiness
- Uses `pg_isready` command to verify database is accepting connections
- `-T` flag disables pseudo-TTY allocation for non-interactive execution

##### 9. Verify Redis Connectivity
```yaml
- name: Verify Redis connectivity
  run: |
    docker compose -f infra/docker-compose.yml exec -T redis redis-cli ping
```
- Tests Redis readiness
- Executes `PING` command in Redis
- Verifies cache layer is operational

##### 10. Verify Kafka Connectivity
```yaml
- name: Verify Kafka connectivity
  run: |
    docker compose -f infra/docker-compose.yml exec -T kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092
```
- Tests Kafka broker readiness
- Verifies message broker is accepting connections

##### 11. Run Backend Tests
```yaml
- name: Run backend tests
  id: backend_tests
  timeout-minutes: 10
  run: |
    docker compose -f infra/docker-compose.yml exec -T backend pytest \
      backend/tests/ \
      -v \
      --tb=short \
      --junit-xml=/tmp/junit.xml \
      --cov=backend \
      --cov-report=xml:/tmp/coverage.xml \
      --cov-report=term \
      -s
```

**Pytest Options**:
- `-v`: Verbose output showing individual test results
- `--tb=short`: Short traceback format for failures
- `--junit-xml=/tmp/junit.xml`: Generate JUnit XML report for GitHub Actions integration
- `--cov=backend`: Code coverage for backend module
- `--cov-report=xml:/tmp/coverage.xml`: Generate Codecov XML report
- `--cov-report=term`: Display coverage in terminal
- `-s`: Show stdout/stderr output from tests

**Test Files**:
- `backend/tests/test_health.py`: Health endpoint tests
- `backend/tests/test_api.py`: API endpoint tests
- `backend/tests/test_websocket.py`: WebSocket functionality tests

**Timeout**: 10 minutes
**Error Handling**: `continue-on-error: true` - proceeds even if tests fail (for log capture)

##### 12. Run Smoke Test - GET /api/v1/streams
```yaml
- name: Run smoke test - GET /api/v1/streams
  id: smoke_test
  timeout-minutes: 5
  run: |
    response=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/v1/streams)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -eq 200 ]; then
      echo "Smoke test passed!"
      exit 0
    fi
```

**Test Details**:
- **Endpoint**: `GET http://localhost:8000/api/v1/streams`
- **Success Criteria**: HTTP 200 response
- **Expected Response**: List of stream objects (may be empty initially)
- **Purpose**: Validates API routing and database query functionality

##### 13. Run Smoke Test - GET /api/v1/health
```yaml
- name: Run smoke test - GET /api/v1/health
  id: health_test
  timeout-minutes: 5
  run: |
    response=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/v1/health)
```

**Test Details**:
- **Endpoint**: `GET http://localhost:8000/api/v1/health`
- **Success Criteria**: HTTP 200 response
- **Expected Response**: Health status with database and Redis connectivity info
- **Purpose**: Validates comprehensive health checks

##### 14. Capture Logs on Failure
```yaml
- name: Capture backend logs on test failure
  if: failure() || steps.backend_tests.outcome == 'failure' || steps.smoke_test.outcome == 'failure'
  run: |
    mkdir -p test-artifacts

    docker compose -f infra/docker-compose.yml logs backend >> test-artifacts/backend-logs.txt 2>&1
    docker compose -f infra/docker-compose.yml logs postgres >> test-artifacts/postgres-logs.txt 2>&1
    docker compose -f infra/docker-compose.yml logs redis >> test-artifacts/redis-logs.txt 2>&1
    docker compose -f infra/docker-compose.yml logs kafka >> test-artifacts/kafka-logs.txt 2>&1
```

**Captured Logs**:
- Backend application logs
- PostgreSQL database logs
- Redis cache logs
- Kafka broker logs
- Docker Compose status
- Network configuration

**Triggers On**:
- Any step failure
- Backend tests failure
- Smoke tests failure

##### 15. Copy Test Results from Container
```yaml
- name: Copy test results from container
  if: always()
  run: |
    docker compose -f infra/docker-compose.yml cp backend:/tmp/junit.xml test-artifacts/junit.xml || true
    docker compose -f infra/docker-compose.yml cp backend:/tmp/coverage.xml test-artifacts/coverage.xml || true
```

**Artifacts Copied**:
- JUnit XML test results
- Coverage XML report

##### 16. Publish Test Results
```yaml
- name: Publish test results
  if: always()
  uses: EnricoMi/publish-unit-test-result-action@v2
```

**Functionality**:
- Publishes test results to GitHub UI
- Displays as check results on PR
- Shows test summary and pass/fail statistics

##### 17. Upload Coverage Reports
```yaml
- name: Upload coverage reports
  if: always()
  uses: codecov/codecov-action@v3
```

**Functionality**:
- Uploads coverage reports to Codecov
- Tracks code coverage trends
- Provides coverage badges for repository

##### 18. Upload Test Artifacts
```yaml
- name: Upload test artifacts
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: test-results-and-logs
    path: test-artifacts/
    retention-days: 30
```

**Retention**: 30 days
**Contents**:
- Test results
- Coverage reports
- Service logs
- Network diagnostics

##### 19. Verify Test Success
```yaml
- name: Verify test success
  if: always()
  run: |
    backend_tests_status="${{ steps.backend_tests.outcome }}"
    smoke_test_status="${{ steps.smoke_test.outcome }}"

    if [ "$backend_tests_status" = "failure" ]; then
      exit 1
    fi

    if [ "$smoke_test_status" = "failure" ]; then
      exit 1
    fi
```

**Checks**:
- Verifies backend tests passed
- Verifies smoke tests passed
- Fails the job if any critical tests failed

##### 20. Tear Down Docker Compose Stack
```yaml
- name: Tear down Docker Compose stack
  if: always()
  run: |
    docker compose -f infra/docker-compose.yml --profile dev down -v
```

**Actions**:
- Stops all containers
- Removes associated volumes (`-v` flag)
- Cleans up network resources
- Prevents resource accumulation between runs

##### 21. Display Test Summary
```yaml
- name: Display test summary
  if: always()
  run: |
    echo "=== CI Pipeline Summary ==="
    echo "Repository: ${{ github.repository }}"
    echo "Branch: ${{ github.ref }}"
    echo "Commit: ${{ github.sha }}"
    echo "Run ID: ${{ github.run_id }}"
```

### Job 2: Quality Gates Check

**Purpose**: Ensures CI job completed successfully

```yaml
quality-gates:
  name: Quality Gates Check
  runs-on: ubuntu-latest
  needs: ci
  if: always()
  steps:
    - name: Check CI Status
      run: |
        if [ "${{ needs.ci.result }}" != "success" ]; then
          exit 1
        fi
```

**Behavior**:
- Only runs after CI job completes
- Fails if CI job failed
- Provides clear quality gates status

### Job 3: Send Notifications

**Purpose**: Reports final workflow status

```yaml
notify:
  name: Send Notifications
  runs-on: ubuntu-latest
  needs: [ci, quality-gates]
  if: always()
```

**Status Reporting**:
- Displays CI status
- Displays quality gates status
- Fails if any job failed

## Environment Variables

The workflow uses the following environment variables from `.env.example`:

```env
# Database
POSTGRES_USER=telemetra
POSTGRES_PASSWORD=telemetra_dev_password
POSTGRES_DB=telemetra
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_URL=redis://redis:6379

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_TOPIC_CHAT=telemetra.events.chat
KAFKA_TOPIC_VIEWER=telemetra.events.viewer
KAFKA_TOPIC_TRANSACTIONS=telemetra.events.transactions
KAFKA_TOPIC_STREAM_META=telemetra.events.stream_meta

# API
API_TITLE=Telemetra API
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
DEBUG=false
LOG_LEVEL=INFO
```

## Health Check Configuration

### Backend Health Endpoint
- **URL**: `http://localhost:8000/health`
- **Method**: GET
- **Success Response**: HTTP 200 with JSON body
- **Retry Logic**: 10 attempts with 10-second delays (100 seconds total)

### Service Health Checks
- **PostgreSQL**: `pg_isready` command
- **Redis**: `redis-cli PING` command
- **Kafka**: `kafka-broker-api-versions.sh` command

## Test Execution Flow

```
1. Checkout code
   |
2. Setup Docker infrastructure
   |
3. Start Docker Compose stack
   |
4. Wait for backend health check
   |
5. Verify all service connectivity
   |
6. Execute pytest tests
   |
7. Execute smoke tests
   |
8. Capture logs (on failure)
   |
9. Publish results
   |
10. Clean up resources
```

## Error Handling and Recovery

### Test Failure Handling
- Backend tests use `continue-on-error: true` to proceed to log capture
- Logs are captured even if tests fail
- Artifacts are uploaded for investigation
- CI job continues to quality gates and notification steps

### Service Startup Failure
- Health check polls with retries before proceeding
- Logs are captured if health check fails
- Job fails immediately if health checks don't pass

### Resource Cleanup
- Docker Compose teardown runs in `if: always()` to ensure cleanup
- Volumes are removed to prevent disk space issues
- Runs even if tests fail

## Performance Considerations

### Image Caching
- Base images are pulled before building to speed up builds
- Docker BuildKit enables faster image building

### Parallel Execution
- All verification steps (database, Redis, Kafka) run sequentially
- Smoke tests run after main tests (depends on backend being ready)

### Timeouts
- **Overall job**: 30 minutes
- **Backend tests**: 10 minutes
- **Smoke tests**: 5 minutes each

## Monitoring and Debugging

### Available Artifacts
After each run, download these artifacts from GitHub Actions:
- `test-results-and-logs/` folder containing:
  - `junit.xml`: Test results in JUnit format
  - `coverage.xml`: Code coverage report
  - `backend-logs.txt`: Backend service logs
  - `postgres-logs.txt`: Database logs
  - `redis-logs.txt`: Cache logs
  - `kafka-logs.txt`: Message broker logs
  - `docker-compose-status.txt`: Container status
  - `network-status.txt`: Docker network configuration

### Codecov Integration
- Coverage reports automatically uploaded to Codecov
- View coverage trends at: `https://codecov.io/gh/telemetra/telemetra`
- Coverage badges can be added to README

### GitHub Check Results
- Test results displayed as GitHub checks
- PR status blocked if tests fail (if branch protection is enabled)
- Detailed test results visible in PR checks tab

## Customization and Extension

### Adding New Tests
1. Add test files to `backend/tests/`
2. Ensure tests follow pytest conventions
3. Tests automatically included in `pytest backend/tests/`

### Adding New Smoke Tests
1. Add curl/httpx commands in the "Run smoke test" steps
2. Each test should validate a critical endpoint
3. Use JSON parsing to validate response format

### Modifying Service Stack
1. Update `infra/docker-compose.yml`
2. Update profile definitions if needed
3. Verify service healthchecks are properly defined

### Changing Health Check Retry Logic
Edit the "Wait for backend health check" step:
```bash
max_attempts=10  # Change number of retries
delay=10         # Change delay in seconds
```

## Integration with Main Branch

### Branch Protection Rules (Recommended)
Enable these GitHub branch protection rules:
1. Require CI workflow to pass before merging
2. Require at least one approval for PR
3. Require status checks to pass
4. Dismiss stale PR approvals

### Code Coverage Requirements
Use Codecov repository settings to:
1. Require minimum coverage threshold
2. Block PRs with coverage decrease
3. Set coverage targets by file

## Troubleshooting

### Health Check Timeout
**Problem**: "Health check failed after 10 attempts"
**Solution**:
1. Check backend logs: `docker compose logs backend`
2. Verify database is running: `docker compose ps`
3. Increase retry count in workflow
4. Check for port conflicts

### Test Failures
**Problem**: "Backend tests failed"
**Solution**:
1. Download `junit.xml` artifact to see specific failures
2. Check `backend-logs.txt` for application errors
3. Verify database has test data
4. Check test isolation (fixtures, mocks)

### Services Not Starting
**Problem**: "Docker Compose services not starting"
**Solution**:
1. Check Docker is available: `docker --version`
2. Check Docker Compose: `docker compose --version`
3. Review `docker-compose-status.txt` artifact
4. Check system resources (disk, memory)

### Network Issues
**Problem**: "Service connectivity failures"
**Solution**:
1. Review `network-status.txt` artifact
2. Check Docker network: `docker network ls`
3. Verify service DNS: `docker compose exec backend nslookup postgres`
4. Check firewall rules

## Best Practices

1. **Regular Monitoring**: Check workflow runs regularly for failures
2. **Artifact Retention**: Download artifacts for failed runs before 30-day expiration
3. **Performance Tuning**: Monitor workflow duration and optimize as needed
4. **Test Maintenance**: Keep tests updated with application changes
5. **Documentation**: Update this file when workflow changes
6. **Secrets Management**: Use GitHub Secrets for sensitive configuration
7. **Test Data**: Ensure test data is properly initialized in fixtures

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.io/)

## Workflow Status Badge

Add this badge to your README.md to display workflow status:

```markdown
[![CI - Backend Tests](https://github.com/telemetra/telemetra/workflows/CI%20-%20Backend%20Tests%20with%20Docker%20Compose/badge.svg?branch=main)](https://github.com/telemetra/telemetra/actions/workflows/ci.yml)
```

## Support and Maintenance

For issues or questions about this workflow:
1. Check this documentation first
2. Review GitHub Actions logs for the specific run
3. Consult workflow artifacts for detailed error information
4. Open an issue with workflow logs and error details
