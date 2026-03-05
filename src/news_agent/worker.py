from __future__ import annotations

import threading
import time

from rq import Worker

from news_agent.config import get_settings
from news_agent.logging import configure_logging
from news_agent.queue import WORKER_HEARTBEAT_KEY, get_queue, get_redis_connection, write_heartbeat


def _heartbeat_loop(ttl_seconds: int) -> None:
    while True:
        write_heartbeat(WORKER_HEARTBEAT_KEY, ttl_seconds)
        time.sleep(30)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    heartbeat_thread = threading.Thread(
        target=_heartbeat_loop,
        args=(settings.worker_heartbeat_ttl_seconds,),
        daemon=True,
    )
    heartbeat_thread.start()

    redis_conn = get_redis_connection()
    queue = get_queue()

    worker = Worker([queue], connection=redis_conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
