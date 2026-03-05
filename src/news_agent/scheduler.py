from __future__ import annotations

from datetime import timezone

from apscheduler.schedulers.blocking import BlockingScheduler

from news_agent.config import get_settings
from news_agent.jobs import poll_subscriptions_job
from news_agent.logging import configure_logging, get_logger
from news_agent.queue import SCHEDULER_HEARTBEAT_KEY, write_heartbeat

logger = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    scheduler = BlockingScheduler(timezone=timezone.utc)

    def poll_and_enqueue() -> None:
        result = poll_subscriptions_job()
        logger.info("scheduler_poll_complete", result=result)

    def heartbeat() -> None:
        write_heartbeat(SCHEDULER_HEARTBEAT_KEY, settings.scheduler_heartbeat_ttl_seconds)

    scheduler.add_job(heartbeat, "interval", seconds=30, id="scheduler-heartbeat", max_instances=1)
    scheduler.add_job(
        poll_and_enqueue,
        "interval",
        minutes=settings.poll_interval_minutes,
        id="scheduler-poll",
        max_instances=1,
        coalesce=True,
    )

    heartbeat()
    scheduler.start()


if __name__ == "__main__":
    main()
