from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from news_agent.db import get_db
from news_agent.health import get_health_status
from news_agent.jobs import process_subscription_job
from news_agent.queue import get_queue
from news_agent.repositories.alerts import list_alert_history
from news_agent.repositories.subscriptions import (
    delete_subscription,
    get_subscription_by_id,
    update_subscription,
    upsert_subscription,
)
from news_agent.schemas import (
    AlertHistoryResponse,
    CreateSubscriptionResponse,
    DeleteSubscriptionResponse,
    HealthStatus,
    RunNowResponse,
    SubscriptionCreateRequest,
    SubscriptionResponse,
    SubscriptionUpdateRequest,
)

router = APIRouter()


@router.post(
    "/v1/subscriptions",
    response_model=CreateSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_subscription(payload: SubscriptionCreateRequest, db: Session = Depends(get_db)):
    subscription, state = upsert_subscription(db, payload)
    return CreateSubscriptionResponse(subscription_id=subscription.id, status=state)


@router.patch("/v1/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
def patch_subscription(
    subscription_id: str,
    payload: SubscriptionUpdateRequest,
    db: Session = Depends(get_db),
):
    subscription = get_subscription_by_id(db, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    updated = update_subscription(db, subscription, payload)
    return SubscriptionResponse.model_validate(updated)


@router.delete("/v1/subscriptions/{subscription_id}", response_model=DeleteSubscriptionResponse)
def remove_subscription(subscription_id: str, db: Session = Depends(get_db)):
    subscription = get_subscription_by_id(db, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    delete_subscription(db, subscription)
    return DeleteSubscriptionResponse(status="deleted")


@router.post("/v1/run-now/{subscription_id}", response_model=RunNowResponse)
def run_now(subscription_id: str, db: Session = Depends(get_db)):
    subscription = get_subscription_by_id(db, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")

    run_id = str(uuid4())
    queue = get_queue()
    queue.enqueue(process_subscription_job, subscription_id, run_id, job_timeout=600)
    return RunNowResponse(run_id=run_id, queued=True)


@router.get("/v1/alerts/history", response_model=AlertHistoryResponse)
def alerts_history(
    subscription_id: str = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    subscription = get_subscription_by_id(db, subscription_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")

    items, total = list_alert_history(db, subscription_id, page=page, page_size=page_size)
    return AlertHistoryResponse(items=items, page=page, page_size=page_size, total=total)


@router.get("/healthz", response_model=HealthStatus)
def healthz():
    return HealthStatus.model_validate(get_health_status())
