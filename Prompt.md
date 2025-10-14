You are Claude Code acting as a multi-agent orchestrator and full-stack engineer.  
I will use the `wshobson/agents` plugin marketplace to coordinate specialized agents in parallel for maximum velocity (install instructions are below). The objective is to **generate a complete, runnable Telemetra MVP** (real-time Twitch analytics) with working Docker Compose dev environment, Spark streaming job, Kafka integration, Postgres schema/migrations, FastAPI backend (with WebSocket), React + D3 frontend, minimal Redis caching, and a simulated Twitch producer — all commit-ready.

IMPORTANT CONTEXT / REQUIREMENTS

- Repo name: `Telemetra`
- Primary goal: `docker compose up` should start all services and present a working dashboard that receives simulated live metrics.
- Use the `wshobson/agents` plugins to run tasks in parallel (install plugin marketplace first). See: https://github.com/wshobson/agents. :contentReference[oaicite:2]{index=2}
- Prioritize the **Docker Compose setup and a working end-to-end demo** (producer → Kafka → Spark → Postgres → API → Frontend) before polishing secondary features.
- Produce real, runnable code (no placeholders for the core dataflow). Small placeholders are OK for heavy ML model code (but include a working lexicon sentiment fallback).
- Produce files structured and ready for a GitHub repo with a clear README, `Makefile` (or scripts), and example `.env.example`.
- Run components and tests in parallel where possible; use the agents to generate and validate concurrently.

PLUGINS TO INSTALL (use the marketplace and then install these plugins to orchestrate tasks)

- `full-stack-development` (backend + frontend orchestration)
- `data-ml-pipeline` (data engineering & streaming + Spark assistance)
- `infrastructure-devops` (docker-compose, k8s manifests)
- `documentation-generation` (README, Mermaid diagrams, OpenAPI)
- `testing-quality-suite` (unit/integration tests + CI config)
- `api-development-kit` (OpenAPI, API scaffolding)
- `database-operations` (schema design, migrations)  
  (These plugin names are available in the wshobson/agents marketplace.) :contentReference[oaicite:3]{index=3}

PARALLEL WORKFLOW (use multi-agent orchestration)

- Stage A (Parallel, high priority):
  - Agent A1: Create a minimal but correct `docker-compose.yml` that brings up: Zookeeper, Kafka, Kafka Schema Registry (or use JSON if simpler), Spark (local/standalone or spark-submit image), Postgres, Redis, FastAPI backend, React frontend, and a simulated Twitch producer (Python script).
  - Agent A2: Scaffold backend FastAPI app with REST + WebSocket endpoints, Dockerfile, and health/metrics endpoints (`/metrics`). Generate an initial CI test that verifies `/health` and a basic WebSocket handshake.
  - Agent A3: Scaffold frontend React app (TypeScript) with a live dashboard page and a D3 component (`ChatRateChart` or `PulseBar`) that connects to the WebSocket and displays simulated data. Include `docker` build setup.
  - Agent A4: Create a Kafka producer script (`twitch_mock_producer.py`) that streams synthetic chat/viewer/transaction events into Kafka for demo. Provide easy env config for frequency and channels.
  - Agent A5: Provide a minimal Spark Structured Streaming job (`spark_streaming_job.py` or Scala) that reads from Kafka topics, aggregates chat per minute, writes aggregates to Postgres (or writes to a Kafka sink that the backend consumes). Ensure the job can run locally (use the official Spark image in docker-compose).
- Stage B (Parallel, medium priority):
  - Agent B1: Schema design and SQL migrations for Postgres tables (`streams`, `chat_summary_minute`, `viewer_timeseries`, `transactions`, `moments`). Provide `alembic` or `sqlx` migration files.
  - Agent B2: Implement Redis caching usage patterns in the backend for low-latency lookups (top chatters, recent viewer count).
  - Agent B3: Add a simple sentiment enricher: lexicon fallback + a commented placeholder for model-based inference. Emit sentiment into `telemetra.derived.sentiment`.
  - Agent B4: Implement simple anomaly detector in Spark (z-score on chat rate) that writes anomalies to a table or Kafka topic.
- Stage C (Parallel, low priority polishing):
  - Agent C1: Generate README, Mermaid architecture diagram, runbook (how to run locally, CLI commands), and sample queries.
  - Agent C2: Create tests (unit tests for backend endpoints, integration test wiring producer → spark → postgres → backend → frontend using a Docker Compose test command). Add GitHub Actions workflow to run these tests.
  - Agent C3: Generate Grafana + Prometheus config and basic dashboards for consumer lag, spark job latency, API latency.
  - Agent C4: Create optional k8s manifests (use manifest templates) and a `deploy/` folder for infra team.

DETAILED DELIVERABLES (exact files & expectations)

- Top-level tree and files (generate these files, not just list):
  telemetra/
  ├── backend/
  │ ├── app/
  │ │ ├── main.py # FastAPI app with REST + WebSocket
  │ │ ├── routes/
  │ │ ├── services/
  │ │ └── models/ # Pydantic models
  │ ├── requirements.txt
  │ └── Dockerfile
  ├── data_pipeline/
  │ ├── producer/
  │ │ └── twitch_mock_producer.py
  │ ├── spark/
  │ │ └── spark_streaming_job.py
  │ ├── schemas/
  │ │ └── kafka_schemas.avsc
  │ └── Dockerfile
  ├── frontend/
  │ ├── src/
  │ │ ├── components/ # D3 components: PulseBar, ChatFlow, EmoteCloud, MomentsTimeline
  │ │ ├── pages/Dashboard.tsx
  │ │ └── App.tsx
  │ ├── package.json
  │ └── Dockerfile
  ├── infra/
  │ ├── docker-compose.yml
  │ ├── prometheus.yml
  │ └── grafana/
  ├── migrations/ # SQL/alembic migrations
  ├── .env.example
  ├── Makefile
  └── README.md

- `docker-compose.yml` must:

  - Provide service names and ports.
  - Mount a volume for Postgres data and Kafka logs.
  - Use an official Spark image (standalone) with ability to `spark-submit` the `spark_streaming_job.py`.
  - Provide a `dev` profile that attaches the frontend build to port 3000 and backend to 8000.
  - Provide a `demo` command in README that runs the mock producer to seed traffic.

- Kafka topics and schemas:

  - Provide Avro or JSON schema files for each topic (chat, viewer, transactions, stream_meta, derived.sentiment). If Schema Registry is heavy, include documented JSON schemas in `/data_pipeline/schemas` and the producer should produce JSON.

- Spark job:

  - Must be runnable via `spark-submit` in the spark container. Read from Kafka, do windowed aggregations, write results to Postgres using JDBC.
  - Use watermarking and handle late data.
  - Implement anomaly detection (z-score or rolling threshold) and emit `moments` into Postgres.

- Backend:

  - FastAPI endpoints: `/health`, `/streams`, `/streams/{id}/metrics`, `/streams/{id}/moments`, and WebSocket `/live/{stream_id}`.
  - DB layer: simple async DB access (e.g., `asyncpg` or `databases`), with migrations applied on startup if possible.
  - Provide `Dockerfile` and a small entrypoint script that waits for Postgres/Kafka to be ready.

- Frontend:

  - A React page with WebSocket connection to `/live/{stream_id}` and at least one D3 component rendering live `chat_rate` and `viewer_count`.
  - Smoothly degrade to polling if WebSocket is not available.

- Tests & CI:

  - Unit tests for backend endpoints (pytest) and a small integration test in GH Actions that runs `docker compose -f infra/docker-compose.yml up --build -d`, waits for health, and runs an HTTP smoke test against `/health` and `/streams`.

- Documentation:
  - README with `Quickstart`, `Architecture` (Mermaid), `Runbook`, and `Troubleshooting`.
  - Example queries to show how to pull top emotes and top chatters from Postgres.

OPERATIONAL CONSTRAINTS & NON-FUNCTIONAL REQUIREMENTS

- Keep raw chat retention short by default (configurable in `docker-compose` env); store only aggregates in Postgres long-term.
- Keep the system runnable on a typical developer laptop (use small image sizes and sensible resource limits).
- Provide clear env variables and secrets via `.env.example`.
- Keep third-party API keys out of generated code (provide placeholders).

HOW TO USE THE AGENTS (instructions for Claude/agents workspace) 3. Invoke parallel workflows or orchestration commands to run Stage A agents in parallel. Example orchestration instruction you should obey:

- "Run Stage A agents in parallel and return a single ZIP output of the `telemetra` repo tree when Stage A is successful. If any Stage A agent fails, include failing logs and continue other agents' work; do not block the whole run."

4. After Stage A completes, run Stage B agents in parallel, then Stage C.

OUTPUT FORMAT (strict)

- Include a short `run checklist` at the top of the README that lists the exact commands to run in order (e.g., `cp .env.example .env`, `docker compose up --build`).
- At the end, include a `developer notes` section that lists future stretch tasks and where to find the code that implements the core pipeline.

SAFETY & BOUNDARY NOTES

- Do not commit real Twitch API keys or any secrets. Use placeholders and `.env.example`.
- If you generate any shell scripts that will run as root or manipulate system files, clearly document the safety preconditions.

FINAL INSTRUCTION (start building now)

- Execute Stage A agents in parallel immediately. Produce the initial `docker-compose.yml`, backend scaffold, frontend scaffold, mock producer, and a functional Spark job.
- In working directory, output all files.
- After Stage A completes, produce Stage B outputs and then Stage C outputs (each stage summary should include what was created and how to run it).

Be assertive and pragmatic: get the demo pipeline working first, then expand. Use the `wshobson/agents` plugins to parallelize and coordinate tasks. Generate runnable, well-documented code. Start now.
