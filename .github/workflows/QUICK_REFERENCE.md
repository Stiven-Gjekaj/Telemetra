# CI/CD Workflow Quick Reference

## Workflow File Location
`.github/workflows/ci.yml`

## Trigger Events
- Push to `main` branch
- Pull request to `main` branch

## Workflow Execution Timeline

| Stage | Duration | Details |
|-------|----------|---------|
| Checkout & Setup | ~2-3 min | Code checkout, Docker setup |
| Pull Base Images | ~3-5 min | Pre-fetch Docker images |
| Start Services | ~5-10 min | Docker Compose startup |
| Health Checks | ~1-2 min | Verify all services ready |
| Backend Tests | ~5-10 min | pytest execution |
| Smoke Tests | ~1-2 min | API endpoint validation |
| Cleanup | ~1 min | Tear down stack |
| **Total** | **~20-35 min** | Full workflow |

## What Gets Tested

### 1. Backend Tests (pytest)
- Health check endpoints
- API endpoints (/api/v1/streams, /api/v1/health, etc.)
- WebSocket functionality
- Error handling
- Database integration

**Location**: `backend/tests/`
**Command**: `pytest backend/tests/ -v --cov=backend`

### 2. Smoke Tests
- `GET /api/v1/streams` (returns 200, list of streams)
- `GET /api/v1/health` (returns 200, health status)

**Validates**:
- API routing works
- Database connectivity
- Response format correctness

### 3. Service Connectivity
- PostgreSQL database
- Redis cache
- Kafka broker
- Zookeeper coordination

## Services Started

| Service | Port | Purpose |
|---------|------|---------|
| Backend API | 8000 | REST API and WebSocket |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache layer |
| Kafka | 9092 | Message broker |
| Zookeeper | 2181 | Kafka coordination |
| Spark Master | 7077 | Distributed computing |
| Spark Worker | 8081 | Worker node |
| Mock Producer | N/A | Test data generation |
| Spark Streaming | N/A | Event processing |

## Health Check Details

### Backend Health Check
```
Endpoint: GET http://localhost:8000/health
Retries: 10 attempts
Delay: 10 seconds between attempts
Max Wait: 100 seconds
```

## Test Artifacts

After each workflow run, these files are available for download:

```
test-results-and-logs/
├── junit.xml                      # Test results in JUnit format
├── coverage.xml                   # Code coverage report
├── backend-logs.txt              # Backend service logs
├── postgres-logs.txt             # Database logs
├── redis-logs.txt                # Cache logs
├── kafka-logs.txt                # Message broker logs
├── docker-compose-status.txt     # Container status
└── network-status.txt            # Network configuration
```

**Retention**: 30 days

## Test Results Integration

### GitHub Checks
- Test results appear as checks on PR
- Individual test results shown in checks tab
- Pass/fail status blocks PR merge (if branch protection enabled)

### Codecov Coverage
- Coverage reports uploaded automatically
- Track coverage trends over time
- Add coverage badge to README

## Common Issues & Solutions

### Health Check Fails
```
Error: "Health check failed after 10 attempts"
Solution:
1. Check backend logs: docker compose logs backend
2. Verify PostgreSQL is running
3. Check Redis connectivity
4. Increase health check timeout
```

### Tests Pass Locally, Fail in CI
```
Possible causes:
1. Environment variable differences
2. Timing/race conditions
3. Database state issues
4. Network configuration

Debug:
1. Download junit.xml and coverage.xml artifacts
2. Review backend-logs.txt for error details
3. Check if tests need fixture data
```

### Services Won't Start
```
Possible causes:
1. Port conflicts on runner
2. Insufficient disk space
3. Docker daemon issues
4. Network issues

Solutions:
1. Check system resources
2. Verify Docker is running
3. Review docker-compose-status.txt
4. Increase timeouts if needed
```

## Performance Tips

1. **Image Caching**: Base images are pre-pulled to speed up builds
2. **Parallel Tests**: Use pytest-xdist plugin for parallel test execution
3. **Conditional Tests**: Mark slow tests with `@pytest.mark.slow`
4. **Coverage Report**: Can be slow; consider incremental coverage

## Configuration Files

### Environment Setup
- **Location**: `.env.example`
- **Copied to**: `.env` during CI
- **Purpose**: Configure services (DB, Redis, Kafka, etc.)

### Docker Compose
- **Location**: `infra/docker-compose.yml`
- **Profile**: `dev` (used in CI)
- **Includes**: All required services for testing

### Backend Tests
- **Location**: `backend/tests/`
- **Pytest Config**: `backend/tests/pytest.ini`
- **Fixtures**: `backend/tests/conftest.py`

## Adding Tests

### New Pytest Tests
1. Create file in `backend/tests/`
2. Follow naming convention: `test_*.py`
3. Use fixtures from `conftest.py`
4. Tests automatically discovered and run

### New Smoke Tests
1. Edit `.github/workflows/ci.yml`
2. Add step: "Run smoke test - GET /api/endpoint"
3. Use curl to call endpoint
4. Validate HTTP status code

### Example Smoke Test
```bash
- name: Run smoke test - GET /custom/endpoint
  run: |
    response=$(curl -s -w "\n%{http_code}" http://localhost:8000/custom/endpoint)
    http_code=$(echo "$response" | tail -n1)

    if [ "$http_code" -eq 200 ]; then
      echo "Test passed!"
      exit 0
    else
      echo "Test failed with HTTP $http_code"
      exit 1
    fi
```

## Monitoring Workflow

### View Workflow Runs
1. Go to GitHub repository
2. Click "Actions" tab
3. Select "CI - Backend Tests with Docker Compose"
4. View run details

### Download Artifacts
1. Click run you want to investigate
2. Scroll to bottom
3. Click "Artifacts"
4. Download `test-results-and-logs` zip file
5. Extract and review logs

### Check Coverage Trends
1. Go to Codecov: https://codecov.io/
2. Select your repository
3. View coverage history and changes

## Branch Protection

To enforce CI workflow passing:

1. Go to repository "Settings"
2. Select "Branches"
3. Click "Add rule"
4. Set branch name pattern: `main`
5. Enable:
   - "Require status checks to pass before merging"
   - Select "CI - Backend Tests" workflow
   - "Require branches to be up to date before merging"
   - "Dismiss stale pull request approvals"

## CI Status Badge

Add to README.md:
```markdown
[![CI - Backend Tests](https://github.com/OWNER/REPO/workflows/CI%20-%20Backend%20Tests%20with%20Docker%20Compose/badge.svg?branch=main)](https://github.com/OWNER/REPO/actions/workflows/ci.yml)
```

## Debugging Tips

### View Real-Time Logs
1. Click workflow run
2. Click "CI - Test Backend with Docker Compose" job
3. Expand specific steps to see logs
4. Watch output in real-time

### Identify Failing Tests
1. Download junit.xml artifact
2. Search for `<failure>` elements
3. Note test name and error message
4. Run test locally: `pytest backend/tests/test_file.py::test_name -v`

### Check Service Connectivity
1. Download docker-compose-status.txt
2. Verify all containers show "healthy" or "running"
3. Check network-status.txt for network details
4. Review service logs for startup errors

### Test Coverage Analysis
1. Download coverage.xml artifact
2. Use coverage tool: `coverage report -m --include=backend`
3. Identify untested code paths
4. Add tests for critical paths

## Useful Commands (Local Development)

```bash
# Start services locally
docker compose -f infra/docker-compose.yml --profile dev up -d

# Run backend tests locally
pytest backend/tests/ -v --cov=backend

# Check specific test
pytest backend/tests/test_health.py -v

# Run tests with output
pytest backend/tests/ -v -s

# Generate coverage report
pytest backend/tests/ --cov=backend --cov-report=html

# Clean up services
docker compose -f infra/docker-compose.yml --profile dev down -v

# View logs
docker compose logs backend
docker compose logs postgres
docker compose logs redis
```

## Performance Metrics

### Average Workflow Duration
- Full workflow: 20-35 minutes
- Most time spent starting services: 10-15 minutes
- Test execution: 5-10 minutes
- Cleanup: 1 minute

### Resource Usage
- Disk space: ~15-20 GB (with Docker images)
- CPU: Varies (up to 100% during tests)
- Memory: ~6-8 GB for full stack

## Maintenance Checklist

- [ ] Review workflow logs weekly
- [ ] Monitor code coverage trends
- [ ] Update tests when API changes
- [ ] Remove skipped/ignored tests
- [ ] Update documentation on changes
- [ ] Check for deprecated GitHub Actions
- [ ] Monitor service versions for updates

## Related Documentation

- Full documentation: `.github/workflows/CI_WORKFLOW_README.md`
- Backend tests: `backend/tests/README.md`
- Docker Compose: `infra/docker-compose.yml`
- Backend API: `backend/README.md`
