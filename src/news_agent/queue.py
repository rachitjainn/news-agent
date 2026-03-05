from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

from redis import Redis
from rq import Queue

from news_agent.config import get_settings

WORKER_HEARTBEAT_KEY = "news_agent:worker_heartbeat"
SCHEDULER_HEARTBEAT_KEY = "news_agent:scheduler_heartbeat"


@lru_cache(maxsize=1)
def get_redis_connection() -> Redis:
    settings = get_settings()
    return Redis.from_url(settings.redis_url, decode_responses=True)


@lru_cache(maxsize=1)
def get_queue() -> Queue:
    settings = get_settings()
    redis_conn = get_redis_connection()
    return Queue(name=settings.queue_name, connection=redis_conn)


def write_heartbeat(key: str, ttl_seconds: int) -> None:
    conn = get_redis_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.setex(key, ttl_seconds, now)
