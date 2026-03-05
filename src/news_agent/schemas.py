from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RawArticle(BaseModel):
    source_id: str
    title: str
    url: str
    published_at: datetime
    snippet: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)


class NormalizedArticle(RawArticle):
    canonical_url: str
    fingerprint: str
    lang: str = "unknown"
    quality_score: float = 0.0


class RankedArticle(NormalizedArticle):
    rule_score: float = 0.0
    llm_score: float = 0.0
    final_score: float = 0.0
    reason: str = ""


class AlertEventPayload(BaseModel):
    subscription_id: str
    article_id: str
    sent_at: datetime
    channel: str
    status: str
    provider_id: str | None = None


class SubscriptionCreateRequest(BaseModel):
    email: EmailStr
    interests: str = Field(min_length=3)
    regions: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    alert_frequency: int = Field(default=15, ge=1, le=1440)


class SubscriptionUpdateRequest(BaseModel):
    interests: str | None = Field(default=None, min_length=3)
    regions: list[str] | None = None
    languages: list[str] | None = None
    alert_frequency: int | None = Field(default=None, ge=1, le=1440)
    is_active: bool | None = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    interests: str
    regions: list[str]
    languages: list[str]
    alert_frequency: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CreateSubscriptionResponse(BaseModel):
    subscription_id: str
    status: Literal["created", "updated"]


class DeleteSubscriptionResponse(BaseModel):
    status: Literal["deleted"]


class RunNowResponse(BaseModel):
    run_id: str
    queued: bool


class AlertEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subscription_id: str
    article_id: str | None
    sent_at: datetime | None
    channel: str
    status: str
    provider_id: str | None
    error: str | None
    run_id: str | None
    created_at: datetime


class AlertHistoryResponse(BaseModel):
    items: list[AlertEventResponse]
    page: int
    page_size: int
    total: int


class HealthStatus(BaseModel):
    api: Literal["ok"]
    worker: Literal["up", "down"]
    scheduler: Literal["up", "down"]
    db: Literal["up", "down"]
    redis: Literal["up", "down"]
