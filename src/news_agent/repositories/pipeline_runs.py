from datetime import datetime, timezone

from sqlalchemy.orm import Session

from news_agent.models import PipelineRun


def create_run(db: Session, subscription_id: str) -> PipelineRun:
    run = PipelineRun(subscription_id=subscription_id, status="started")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def complete_run(
    db: Session,
    run: PipelineRun,
    *,
    status: str,
    articles_fetched: int,
    articles_ranked: int,
    alerts_sent: int,
    error: str | None = None,
) -> None:
    run.status = status
    run.finished_at = datetime.now(timezone.utc)
    run.articles_fetched = articles_fetched
    run.articles_ranked = articles_ranked
    run.alerts_sent = alerts_sent
    run.error = error
    db.commit()
