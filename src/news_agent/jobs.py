from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from news_agent.config import get_settings
from news_agent.db import get_session_factory
from news_agent.logging import configure_logging, get_logger
from news_agent.models import Subscription
from news_agent.queue import get_queue
from news_agent.repositories.pipeline_runs import complete_run, create_run
from news_agent.repositories.subscriptions import get_subscription_by_id, list_active_subscriptions
from news_agent.services.pipeline import PipelineOrchestrator

logger = get_logger(__name__)


def process_subscription_job(subscription_id: str, run_id: str | None = None) -> dict[str, object]:
    configure_logging(get_settings().log_level)
    run_id = run_id or str(uuid4())

    session_factory = get_session_factory()
    db = session_factory()
    try:
        subscription = get_subscription_by_id(db, subscription_id)
        if subscription is None or not subscription.is_active:
            return {"run_id": run_id, "status": "skipped", "reason": "subscription_not_found_or_inactive"}

        run = create_run(db, subscription.id)
        orchestrator = PipelineOrchestrator()
        try:
            result = orchestrator.process_subscription(db, subscription, run_id=run_id)
            complete_run(
                db,
                run,
                status="success",
                articles_fetched=int(result["articles_fetched"]),
                articles_ranked=int(result["articles_ranked"]),
                alerts_sent=int(result["alerts_sent"]),
            )
            return {"run_id": run_id, "status": "success", **result}
        except Exception as exc:  # noqa: BLE001
            complete_run(
                db,
                run,
                status="failed",
                articles_fetched=0,
                articles_ranked=0,
                alerts_sent=0,
                error=str(exc),
            )
            logger.error("subscription_job_failed", subscription_id=subscription_id, error=str(exc))
            return {"run_id": run_id, "status": "failed", "error": str(exc)}
    finally:
        db.close()


def poll_subscriptions_job() -> dict[str, object]:
    configure_logging(get_settings().log_level)
    queue = get_queue()
    session_factory = get_session_factory()
    db = session_factory()
    enqueued = 0

    try:
        subscriptions: list[Subscription] = list_active_subscriptions(db)
        for sub in subscriptions:
            run_id = str(uuid4())
            queue.enqueue(process_subscription_job, sub.id, run_id, job_timeout=600)
            enqueued += 1

        return {
            "status": "enqueued",
            "count": enqueued,
            "queued_at": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()
