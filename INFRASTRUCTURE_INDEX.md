# Telemetra Infrastructure Index

Navigation guide for all infrastructure documentation and configuration files.

## Quick Access

### I need to...
- **Get started in 5 minutes** → `QUICKSTART.md`
- **Understand the full setup** → `INFRASTRUCTURE_SUMMARY.md`
- **Deploy and verify everything** → `DEPLOYMENT_CHECKLIST.md`
- **Configure the system** → `infra/CONFIGURATION.md`
- **Know what each service does** → `infra/SERVICES.md`
- **Set up infrastructure manually** → `infra/README.md`

## File Structure

### Root Level Documentation

```
QUICKSTART.md
├─ Purpose: Get running in 5 minutes
├─ Contents:
│  ├─ 60-second setup command
│  ├─ Service verification
│  ├─ Common tasks (logs, database, cleanup)
│  ├─ Resource requirements
│  ├─ Troubleshooting quick fixes
│  └─ Next steps
└─ Read time: 3 minutes

INFRASTRUCTURE_SUMMARY.md
├─ Purpose: Overview of all created infrastructure
├─ Contents:
│  ├─ What was created (11 files)
│  ├─ Quick start recap
│  ├─ Service architecture diagram
│  ├─ Resource requirements
│  ├─ Network topology
│  ├─ Configuration management
│  ├─ Troubleshooting reference
│  ├─ Maintenance procedures
│  ├─ Performance tuning
│  └─ Next steps
└─ Read time: 8 minutes

DEPLOYMENT_CHECKLIST.md
├─ Purpose: Step-by-step deployment verification
├─ Contents:
│  ├─ Pre-deployment checklist
│  ├─ Environment setup steps
│  ├─ Docker build verification
│  ├─ Service startup verification
│  ├─ Infrastructure validation
│  │  ├─ Kafka setup
│  │  ├─ PostgreSQL setup
│  │  └─ Redis setup
│  ├─ Application services validation
│  │  ├─ Backend API
│  │  ├─ WebSocket
│  │  └─ Frontend
│  ├─ Data pipeline validation
│  ├─ Performance & resource checks
│  ├─ Logs inspection
│  ├─ Integration testing
│  ├─ Cleanup & shutdown
│  ├─ Troubleshooting guide
│  └─ Sign-off section
└─ Read time: 15 minutes (complete execution: 30 minutes)

INFRASTRUCTURE_INDEX.md (this file)
├─ Purpose: Navigation guide
├─ Contents:
│  ├─ Quick access table
│  ├─ File structure overview
│  ├─ Decision tree
│  ├─ Common workflows
│  └─ Reference materials
└─ Read time: 5 minutes
```

### Configuration Files

```
.env.example
├─ Purpose: Environment variable template
├─ Sections:
│  ├─ PostgreSQL
│  ├─ Kafka
│  ├─ Mock Producer
│  ├─ Backend
│  ├─ Frontend
│  ├─ General (logging, debug)
│  ├─ pgAdmin
│  ├─ Spark
│  └─ Streaming
├─ Usage: cp .env.example .env
└─ File size: 1.3 KB

Makefile
├─ Purpose: Convenient command shortcuts
├─ Commands:
│  ├─ setup, build, up, down, restart
│  ├─ logs, ps, health-check
│  ├─ test, test-integration
│  ├─ kafka-topics, kafka-consume
│  ├─ db-shell, redis-shell
│  └─ clean, clean-volumes, clean-all
├─ Usage: make [command]
└─ File size: 5.2 KB
```

### Infrastructure Directory (`infra/`)

```
infra/docker-compose.yml
├─ Purpose: Main service definitions
├─ Contents:
│  ├─ 10 services + optional 2
│  ├─ 2 profiles (dev, full)
│  ├─ Health checks for all services
│  ├─ Startup dependencies
│  ├─ Resource limits and reservations
│  ├─ Volume definitions
│  └─ Network configuration
├─ Profiles:
│  ├─ dev: Essential services (~12 CPU, 11.5GB)
│  └─ full: dev + monitoring (Kafka UI, pgAdmin)
└─ File size: 11 KB

infra/init-db.sql
├─ Purpose: PostgreSQL schema initialization
├─ Contents:
│  ├─ 5 main tables (streams, chat_summary_minute, viewer_timeseries, transactions, moments)
│  ├─ Indexes for performance
│  ├─ Materialized views (top chatters, anomalies)
│  ├─ Triggers for timestamps
│  └─ Demo data insertion
├─ Auto-runs: On first PostgreSQL startup
└─ File size: 4.6 KB

infra/README.md
├─ Purpose: Detailed infrastructure documentation
├─ Contents:
│  ├─ Quick start (copy-paste commands)
│  ├─ Architecture diagram
│  ├─ Service descriptions (purpose, ports, config)
│  ├─ Resource limits table
│  ├─ Configuration management
│  ├─ Profiles explanation
│  ├─ Common operations (using Make and manual docker-compose)
│  ├─ Troubleshooting (9 scenarios with solutions)
│  ├─ Network topology
│  ├─ Volume management
│  ├─ Performance tuning
│  ├─ Health checks
│  └─ Next steps
├─ Read this if: You want complete infrastructure details
└─ File size: 17 KB

infra/CONFIGURATION.md
├─ Purpose: Complete configuration reference
├─ Contents:
│  ├─ All environment variables documented
│  │  ├─ Database, Kafka, Producer, Backend, Frontend
│  │  ├─ Logging, Admin, Spark, Streaming
│  ├─ Default values for each variable
│  ├─ Data types and ranges
│  ├─ Examples and use cases
│  ├─ Security notes
│  ├─ Configuration examples (dev, load test, prod, debug)
│  ├─ Configuration validation
│  ├─ Changing configuration (what requires restart)
│  ├─ Performance tuning by use case
│  └─ Security considerations
├─ Read this if: You want to customize behavior
└─ File size: 12 KB

infra/SERVICES.md
├─ Purpose: Service-by-service reference
├─ Contents:
│  ├─ Service overview by tier
│  ├─ Detailed descriptions for each service:
│  │  ├─ Docker image, container name, ports
│  │  ├─ Purpose and role
│  │  ├─ Configuration
│  │  ├─ Health check procedures
│  │  ├─ Dependencies
│  │  ├─ Use cases
│  ├─ Optional services (Kafka UI, pgAdmin)
│  ├─ Startup order diagram
│  ├─ Service communication map
│  ├─ Performance characteristics table
│  ├─ Logging procedures
│  ├─ Environment variables per service
│  └─ Troubleshooting by service
├─ Read this if: You need details about a specific service
└─ File size: 20 KB

infra/entrypoint.sh
├─ Purpose: Automated startup script
├─ Features:
│  ├─ Environment validation
│  ├─ Docker check
│  ├─ Image building
│  ├─ Service health polling
│  ├─ Clear error messages
│  ├─ Startup summary
├─ Usage: ./infra/entrypoint.sh dev
└─ File size: 4 KB

infra/wait-for-it.sh
├─ Purpose: Service dependency waiter
├─ Features:
│  ├─ TCP port availability check
│  ├─ Configurable timeout
│  ├─ Quiet mode
│  ├─ Command chaining
├─ Usage: ./infra/wait-for-it.sh localhost:5432
└─ File size: 1.3 KB
```

## Decision Tree

### "I want to..."

#### Start the services
```
Quick method:
  1. cp .env.example .env
  2. docker compose -f infra/docker-compose.yml --profile dev up -d
  3. open http://localhost:3000

Using Make:
  1. make setup
  2. make up
  3. open http://localhost:3000

Automated with script:
  1. cp .env.example .env
  2. bash infra/entrypoint.sh dev
```

#### Learn the system
```
→ QUICKSTART.md (5 min read, working in 5 minutes)
→ INFRASTRUCTURE_SUMMARY.md (8 min read, overview)
→ infra/README.md (20 min read, complete guide)
```

#### Configure the system
```
→ .env.example (see all variables)
→ infra/CONFIGURATION.md (understand each variable)
→ Edit .env
→ Restart relevant services
```

#### Verify everything works
```
Quick:
  curl http://localhost:8000/health

Complete:
  Follow DEPLOYMENT_CHECKLIST.md (30 minutes)

Using Make:
  make health-check
```

#### Monitor the system
```
Logs:
  make logs
  make logs-backend
  docker compose -f infra/docker-compose.yml logs -f

Status:
  make ps
  docker compose -f infra/docker-compose.yml ps

Resources:
  docker stats
```

#### Troubleshoot a problem
```
Quick diagnostic:
  docker compose -f infra/docker-compose.yml ps
  docker compose -f infra/docker-compose.yml logs --tail=50

Specific service:
  make logs-[service]
  docker compose -f infra/docker-compose.yml logs [service]

Detailed guide:
  See "Troubleshooting" sections in infra/README.md
  Or DEPLOYMENT_CHECKLIST.md
```

#### Stop the services
```
Keep data:
  docker compose -f infra/docker-compose.yml down
  Or: make down

Remove data:
  docker compose -f infra/docker-compose.yml down -v
  Or: make clean-volumes

Remove everything:
  docker compose -f infra/docker-compose.yml down -v --remove-orphans --rmi all
  Or: make clean-all
```

## Common Workflows

### Development Workflow
```bash
# 1. Start once
cp .env.example .env
make up

# 2. Make code changes in IDE

# 3. Rebuild specific service
docker compose -f infra/docker-compose.yml build backend --no-cache
docker compose -f infra/docker-compose.yml restart backend

# 4. Check logs
make logs-backend

# 5. Stop when done
make down
```

### Load Testing Workflow
```bash
# 1. Increase producer rate in .env
PRODUCER_RATE_PER_SEC=100
make restart

# 2. Monitor performance
docker stats

# 3. Check data flow
docker compose -f infra/docker-compose.yml logs -f spark-streaming-job

# 4. Verify database
docker compose -f infra/docker-compose.yml exec postgres psql \
  -U telemetra -d telemetra -c "SELECT COUNT(*) FROM chat_summary_minute;"

# 5. Stop
make down
```

### Debugging Workflow
```bash
# 1. Enable debug logging in .env
DEBUG=true
LOG_LEVEL=DEBUG
make restart

# 2. View detailed logs
make logs

# 3. Access database
make db-shell
SELECT * FROM moments ORDER BY timestamp DESC LIMIT 10;

# 4. Access Kafka
make kafka-consume

# 5. Disable debug and restart
DEBUG=false
LOG_LEVEL=INFO
make restart
```

### First-Time Setup Workflow
```bash
# 1. Quick start
make setup
make up

# 2. Verify (takes ~5 minutes for all services)
sleep 30  # Wait for startup
make health-check

# 3. Check dashboard
open http://localhost:3000

# 4. Run deployment checklist (optional, comprehensive)
# Follow DEPLOYMENT_CHECKLIST.md for complete verification
```

## Reference Materials

### Configuration
- **All variables**: `infra/CONFIGURATION.md`
- **Default values**: `.env.example`
- **Edit values**: `.env` (copy from example first)

### Documentation
- **5-minute start**: `QUICKSTART.md`
- **Complete guide**: `infra/README.md`
- **Deployment steps**: `DEPLOYMENT_CHECKLIST.md`
- **Service details**: `infra/SERVICES.md`
- **Summary**: `INFRASTRUCTURE_SUMMARY.md`

### Services
- **All services defined in**: `infra/docker-compose.yml`
- **Database schema**: `infra/init-db.sql`
- **Startup automation**: `infra/entrypoint.sh`
- **Service waiting**: `infra/wait-for-it.sh`

### Commands
- **Convenient shortcuts**: `Makefile`
- **Direct Docker**: `docker compose -f infra/docker-compose.yml [command]`

## File Relationships

```
User starts here:
    ↓
    QUICKSTART.md (5 min to running services)
    ↓
    ├─ Understand system → INFRASTRUCTURE_SUMMARY.md
    ├─ Need more details → infra/README.md
    ├─ Configure → .env.example + infra/CONFIGURATION.md
    ├─ Verify → DEPLOYMENT_CHECKLIST.md
    └─ Deep dive → infra/SERVICES.md

Technical reference:
    ├─ Services → infra/SERVICES.md
    ├─ Configuration → infra/CONFIGURATION.md
    └─ Commands → Makefile + infra/README.md

Troubleshooting:
    ├─ Quick fixes → QUICKSTART.md or infra/README.md
    └─ Complete guide → DEPLOYMENT_CHECKLIST.md
```

## Key Statistics

### Infrastructure
- **Services**: 12 (10 core + 2 optional)
- **Profiles**: 2 (dev, full)
- **Ports**: 10+ exposed (3000, 8000, 8080, 8888, 5050, 9092, 5432, 6379, 7077, 2181)
- **Volumes**: 2 persistent (PostgreSQL, Redis)
- **Total resources**: 12 CPU cores, 11.5GB memory (dev profile)

### Documentation
- **Files created**: 11
- **Total documentation**: ~60 KB
- **Coverage**: Setup, configuration, troubleshooting, services, deployment

### Configuration
- **Environment variables**: 30+
- **Customizable parameters**: 15+
- **Configuration examples**: 4 (dev, load test, production, debug)

## Support

### If you need...
- **Quick start**: `QUICKSTART.md`
- **Complete setup guide**: `infra/README.md`
- **Configuration help**: `infra/CONFIGURATION.md`
- **Service details**: `infra/SERVICES.md`
- **Deployment verification**: `DEPLOYMENT_CHECKLIST.md`
- **System overview**: `INFRASTRUCTURE_SUMMARY.md`
- **Command shortcuts**: `Makefile` + `make help`

### Quick Commands
```bash
make help           # All available commands
make up             # Start services
make logs           # View logs
make health-check   # Verify health
make down           # Stop services
```

---

**Start here**: `QUICKSTART.md` (5 minutes to running services)

**Then read**: Choose based on your needs:
- `INFRASTRUCTURE_SUMMARY.md` - System overview
- `infra/README.md` - Detailed guide
- `infra/CONFIGURATION.md` - Configuration options
- `infra/SERVICES.md` - Service reference
