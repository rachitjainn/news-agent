# News Agent (Local-First Runbook)

This repository contains a Python news agent with:
- FastAPI API
- RQ worker
- APScheduler poller
- PostgreSQL + Redis
- Source ingestion (RSS, Hacker News, GitHub, optional GNews)
- Dedup, ranking, and email alerting

## Local Prerequisites

- Python 3.12+
- Docker + Docker Compose
- `make` (optional, but recommended)

## Run Everything Locally (Recommended)

1. Bootstrap dependencies and DB schema:

```bash
make bootstrap
```

2. Start API + worker + scheduler together:

```bash
make run-local
```

3. Open the API:

- `http://localhost:8000/healthz`
- `http://localhost:8000/metrics`
- `http://localhost:8000/dashboard`

4. Stop all app processes with `Ctrl+C` in the `make run-local` terminal.

## What `make bootstrap` Does

- Creates `.env` from `.env.example` if missing
- Installs project in editable mode with dev dependencies
- Starts local Postgres and Redis via Docker
- Waits until Postgres accepts connections
- Runs Alembic migrations

## Manual Run (If You Prefer Separate Terminals)

1. Setup + infra:

```bash
make bootstrap
```

2. Terminal A:

```bash
make api
```

3. Terminal B:

```bash
make worker
```

4. Terminal C:

```bash
make scheduler
```

## Local Logs

When using `make run-local`, logs are written to:
- `.local/api.log`
- `.local/worker.log`
- `.local/scheduler.log`

## Quick API Smoke Test

Create a subscription:

```bash
curl -X POST http://localhost:8000/v1/subscriptions \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "you@example.com",
    "interests": "AI, developer tools, open source",
    "regions": ["us"],
    "languages": ["en"],
    "alert_frequency": 15
  }'
```

Trigger immediate run:

```bash
curl -X POST http://localhost:8000/v1/run-now/<subscription_id>
```

Read alert history:

```bash
curl "http://localhost:8000/v1/alerts/history?subscription_id=<subscription_id>"
```

## Environment Notes

- If `SMTP_HOST` is empty, sends run in dry-run mode (no real email dispatch).
- Set `OPENAI_API_KEY` and keep `ENABLE_LLM=true` to enable LLM scoring.
- Add `GNEWS_API_KEY` to enable the GNews adapter.

## API Keys / Secrets You Should Set

Required for real email delivery:
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `FROM_EMAIL`

Strongly recommended:
- `OPENAI_API_KEY` (for better ranking quality)
- `GITHUB_TOKEN` (avoids strict anonymous GitHub rate limits)

Optional:
- `GNEWS_API_KEY` (adds one extra news source)

No key needed:
- RSS feeds
- Hacker News source

## Useful Commands

```bash
make test
make lint
make deps-down
```

## Troubleshooting

- If DB migration fails, inspect infra status:

```bash
docker compose ps
docker compose logs postgres --tail 100
```

- Re-run only migration step:

```bash
make migrate
```

## Core Files

- `src/news_agent/main.py` (FastAPI app)
- `src/news_agent/api/routes.py` (REST endpoints)
- `src/news_agent/services/pipeline.py` (orchestration)
- `src/news_agent/worker.py` (RQ worker)
- `src/news_agent/scheduler.py` (poll scheduler)
- `docker-compose.yml` (local Postgres/Redis)
- `scripts/run_local.sh` (run all app processes locally)
