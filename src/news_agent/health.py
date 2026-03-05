from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from news_agent.config import get_settings
from news_agent.db import get_session_factory
from news_agent.queue import (
    SCHEDULER_HEARTBEAT_KEY,
    WORKER_HEARTBEAT_KEY,
    get_redis_connection,
)


def _heartbeat_status(iso_timestamp: str | None, ttl_seconds: int) -> str:
    if not iso_timestamp:
        return "down"
    try:
        ts = datetime.fromisoformat(iso_timestamp)
    except ValueError:
        return "down"
    age = (datetime.now(timezone.utc) - ts).total_seconds()
    return "up" if age <= ttl_seconds else "down"


def get_health_status() -> dict[str, str]:
    settings = get_settings()

    db_status = "up"
    try:
        session = get_session_factory()()
        session.execute(text("SELECT 1"))
        session.close()
    except SQLAlchemyError:
        db_status = "down"

    redis_status = "up"
    worker_status = "down"
    scheduler_status = "down"

    try:
        redis_conn = get_redis_connection()
        redis_conn.ping()
        worker_ts = redis_conn.get(WORKER_HEARTBEAT_KEY)
        scheduler_ts = redis_conn.get(SCHEDULER_HEARTBEAT_KEY)
        worker_status = _heartbeat_status(worker_ts, settings.worker_heartbeat_ttl_seconds)
        scheduler_status = _heartbeat_status(scheduler_ts, settings.scheduler_heartbeat_ttl_seconds)
    except Exception:  # noqa: BLE001
        redis_status = "down"

    return {
        "api": "ok",
        "worker": worker_status,
        "scheduler": scheduler_status,
        "db": db_status,
        "redis": redis_status,
    }
