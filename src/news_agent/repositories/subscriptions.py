from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from news_agent.models import Subscription
from news_agent.schemas import SubscriptionCreateRequest, SubscriptionUpdateRequest


def upsert_subscription(db: Session, payload: SubscriptionCreateRequest) -> tuple[Subscription, str]:
    subscription = db.execute(
        select(Subscription).where(Subscription.email == payload.email)
    ).scalar_one_or_none()

    if subscription is None:
        subscription = Subscription(
            email=str(payload.email),
            interests=payload.interests,
            regions=payload.regions,
            languages=payload.languages,
            alert_frequency=payload.alert_frequency,
            is_active=True,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription, "created"

    subscription.interests = payload.interests
    subscription.regions = payload.regions
    subscription.languages = payload.languages
    subscription.alert_frequency = payload.alert_frequency
    subscription.is_active = True
    subscription.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(subscription)
    return subscription, "updated"


def get_subscription_by_id(db: Session, subscription_id: str) -> Subscription | None:
    return db.get(Subscription, subscription_id)


def update_subscription(
    db: Session,
    subscription: Subscription,
    payload: SubscriptionUpdateRequest,
) -> Subscription:
    if payload.interests is not None:
        subscription.interests = payload.interests
    if payload.regions is not None:
        subscription.regions = payload.regions
    if payload.languages is not None:
        subscription.languages = payload.languages
    if payload.alert_frequency is not None:
        subscription.alert_frequency = payload.alert_frequency
    if payload.is_active is not None:
        subscription.is_active = payload.is_active
    subscription.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(subscription)
    return subscription


def delete_subscription(db: Session, subscription: Subscription) -> None:
    db.delete(subscription)
    db.commit()


def list_active_subscriptions(db: Session) -> list[Subscription]:
    result = db.execute(select(Subscription).where(Subscription.is_active.is_(True)))
    return list(result.scalars().all())


def mark_polled(db: Session, subscription: Subscription) -> None:
    subscription.last_polled_at = datetime.now(timezone.utc)
    db.commit()


def mark_alert_sent(db: Session, subscription: Subscription) -> None:
    subscription.last_alert_sent_at = datetime.now(timezone.utc)
    db.commit()
