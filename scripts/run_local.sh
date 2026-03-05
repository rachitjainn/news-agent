#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/.local"
mkdir -p "$LOG_DIR"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "Created .env from .env.example"
fi

cleanup() {
  local exit_code=$?

  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "${WORKER_PID:-}" ]] && kill -0 "$WORKER_PID" 2>/dev/null; then
    kill "$WORKER_PID" 2>/dev/null || true
  fi
  if [[ -n "${SCHEDULER_PID:-}" ]] && kill -0 "$SCHEDULER_PID" 2>/dev/null; then
    kill "$SCHEDULER_PID" 2>/dev/null || true
  fi

  wait 2>/dev/null || true
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

news-agent-worker >"$LOG_DIR/worker.log" 2>&1 &
WORKER_PID=$!

news-agent-scheduler >"$LOG_DIR/scheduler.log" 2>&1 &
SCHEDULER_PID=$!

news-agent-api >"$LOG_DIR/api.log" 2>&1 &
API_PID=$!

echo "Local services started"
echo "API log: $LOG_DIR/api.log"
echo "Worker log: $LOG_DIR/worker.log"
echo "Scheduler log: $LOG_DIR/scheduler.log"
echo "API URL: http://localhost:8000"
echo "Press Ctrl+C to stop all"

while true; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "API process exited. Check $LOG_DIR/api.log"
    exit 1
  fi
  if ! kill -0 "$WORKER_PID" 2>/dev/null; then
    echo "Worker process exited. Check $LOG_DIR/worker.log"
    exit 1
  fi
  if ! kill -0 "$SCHEDULER_PID" 2>/dev/null; then
    echo "Scheduler process exited. Check $LOG_DIR/scheduler.log"
    exit 1
  fi
  sleep 2
done
