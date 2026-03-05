from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from news_agent.models import AlertEvent


def create_alert_event(
    db: Session,
    subscription_id: str,
    article_id: str | None,
    channel: str,
    status: str,
    run_id: str | None = None,
    provider_id: str | None = None,
    error: str | None = None,
    sent_at: datetime | None = None,
) -> AlertEvent | None:
    event = AlertEvent(
        subscription_id=subscription_id,
        article_id=article_id,
        channel=channel,
        status=status,
        run_id=run_id,
        provider_id=provider_id,
        error=error,
        sent_at=sent_at,
    )
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
        return event
    except IntegrityError:
        db.rollback()
        return None


def event_exists(db: Session, subscription_id: str, article_id: str, channel: str = "email") -> bool:
    count = db.execute(
        select(func.count(AlertEvent.id)).where(
            AlertEvent.subscription_id == subscription_id,
            AlertEvent.article_id == article_id,
            AlertEvent.channel == channel,
            AlertEvent.status == "sent",
        )
    ).scalar_one()
    return count > 0


def list_alert_history(
    db: Session,
    subscription_id: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AlertEvent], int]:
    page = max(page, 1)
    page_size = max(min(page_size, 100), 1)
    offset = (page - 1) * page_size

    total = db.execute(
        select(func.count(AlertEvent.id)).where(AlertEvent.subscription_id == subscription_id)
    ).scalar_one()

    items = db.execute(
        select(AlertEvent)
        .where(AlertEvent.subscription_id == subscription_id)
        .order_by(AlertEvent.created_at.desc())
        .offset(offset)
        .limit(page_size)
    ).scalars()

    return list(items), int(total)


def create_debounced_events(
    db: Session,
    subscription_id: str,
    article_ids: list[str],
    channel: str,
    run_id: str,
) -> None:
    for article_id in article_ids:
        create_alert_event(
            db=db,
            subscription_id=subscription_id,
            article_id=article_id,
            channel=channel,
            status="debounced",
            run_id=run_id,
            sent_at=datetime.now(timezone.utc),
        )
