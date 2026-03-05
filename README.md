# News Agent (Python-First)

24/7 VPS-ready news monitoring service with:
- FastAPI API for subscriptions and control endpoints
- Source ingestion from RSS, Hacker News, GitHub, and optional GNews
- Normalization + deduplication
- Hybrid ranking (rules + optional OpenAI scoring)
- Instant email alerts with debounce + idempotency
- Redis queue (RQ) worker + APScheduler poller
- PostgreSQL persistence + Alembic migrations
- Prometheus metrics and health checks

## Project Layout

- `src/news_agent/main.py`: FastAPI app
- `src/news_agent/api/routes.py`: API endpoints
- `src/news_agent/models.py`: SQLAlchemy models
- `src/news_agent/services/pipeline.py`: orchestrator
- `src/news_agent/services/normalize.py`: canonicalization/dedup helpers
- `src/news_agent/services/ranking.py`: rules + LLM ranking
- `src/news_agent/services/alerting.py`: email dispatch + debounce
- `src/news_agent/sources/`: source adapters
- `src/news_agent/jobs.py`: queue jobs
- `src/news_agent/worker.py`: RQ worker entrypoint
- `src/news_agent/scheduler.py`: APScheduler entrypoint
- `alembic/`: DB migration setup

## API Endpoints

- `POST /v1/subscriptions`
- `PATCH /v1/subscriptions/{id}`
- `DELETE /v1/subscriptions/{id}`
- `POST /v1/run-now/{subscription_id}`
- `GET /v1/alerts/history?subscription_id=...`
- `GET /healthz`
- `GET /metrics`

## Quickstart

1. Copy env:

```bash
cp .env.example .env
```

2. Install:

```bash
python3 -m pip install -e '.[dev]'
```

3. Start dependencies:

```bash
docker compose up -d postgres redis
```

4. Run migrations:

```bash
alembic upgrade head
```

5. Start API:

```bash
news-agent-api
```

6. Start worker (new terminal):

```bash
news-agent-worker
```

7. Start scheduler (new terminal):

```bash
news-agent-scheduler
```

## Docker Compose (Full Stack)

```bash
docker compose up --build
```

Services:
- API on `http://localhost:8000`
- Postgres on `localhost:5432`
- Redis on `localhost:6379`

## Testing

```bash
pytest -q
```

## Notes

- If `SMTP_HOST` is empty, email delivery runs in dry-run mode and logs alert sends without external SMTP.
- Set `OPENAI_API_KEY` and `ENABLE_LLM=true` to enable LLM scoring for top candidates.
- `healthz` worker/scheduler status comes from Redis heartbeats written by worker/scheduler processes.
