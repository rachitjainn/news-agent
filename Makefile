.PHONY: setup deps-up deps-down wait-db migrate api worker scheduler run-local test lint bootstrap

setup:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	python3 -m pip install -e '.[dev]'

deps-up:
	docker compose up -d postgres redis

deps-down:
	docker compose stop postgres redis

wait-db:
	@if [ -f .env ]; then set -a; . ./.env; set +a; fi; \
	python3 scripts/wait_for_postgres.py

migrate: wait-db
	alembic upgrade head

bootstrap: setup deps-up migrate

api:
	news-agent-api

worker:
	news-agent-worker

scheduler:
	news-agent-scheduler

run-local:
	./scripts/run_local.sh

test:
	pytest -q

lint:
	ruff check src tests
