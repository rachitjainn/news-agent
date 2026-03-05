from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from news_agent.config import get_settings
from news_agent.logging import get_logger
from news_agent.models import Article, Subscription
from news_agent.observability import (
    increment_alerts_sent,
    increment_articles_fetched,
    increment_articles_ranked,
    increment_source_error,
)
from news_agent.repositories.articles import find_existing_fingerprints, upsert_articles
from news_agent.repositories.subscriptions import mark_polled
from news_agent.schemas import RankedArticle, RawArticle
from news_agent.services.alerting import EmailAlertService
from news_agent.services.normalize import build_query_profile, normalize_articles
from news_agent.services.ranking import rank_articles
from news_agent.sources.registry import build_source_registry

logger = get_logger(__name__)


class PipelineResult(dict):
    articles_fetched: int
    articles_ranked: int
    alerts_sent: int


class PipelineOrchestrator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.sources = build_source_registry()
        self.alert_service = EmailAlertService()

    def _fetch_raw_articles(
        self,
        since_ts: datetime,
        query_profile: dict[str, object],
    ) -> list[RawArticle]:
        fetched: list[RawArticle] = []
        for source in self.sources:
            try:
                articles = source.fetch(since_ts, query_profile)
                fetched.extend(articles)
                increment_articles_fetched(source.name, len(articles))
            except Exception as exc:  # noqa: BLE001
                logger.warning("source_fetch_failed", source=source.name, error=str(exc))
                increment_source_error(source.name)
        return fetched

    def process_subscription(
        self,
        db: Session,
        subscription: Subscription,
        run_id: str,
    ) -> PipelineResult:
        now = datetime.now(timezone.utc)
        since_ts = subscription.last_polled_at or (now - timedelta(hours=6))
        query_profile = build_query_profile(
            interests=subscription.interests,
            regions=subscription.regions,
            languages=subscription.languages,
            now=now,
        )

        raw_articles = self._fetch_raw_articles(since_ts, query_profile)
        if len(raw_articles) > self.settings.max_fetch_articles:
            raw_articles = raw_articles[: self.settings.max_fetch_articles]

        normalized = normalize_articles(raw_articles)
        existing = find_existing_fingerprints(
            db,
            [article.fingerprint for article in normalized],
            window_hours=24,
        )
        deduped = [article for article in normalized if article.fingerprint not in existing]

        stored_articles = upsert_articles(db, deduped)
        stored_map: dict[str, Article] = {article.canonical_url: article for article in stored_articles}

        ranked: list[RankedArticle] = rank_articles(deduped, query_profile)
        increment_articles_ranked(len(ranked))

        alerts_sent = self.alert_service.send_alerts(
            db=db,
            subscription=subscription,
            ranked_articles=ranked,
            stored_articles=stored_map,
            run_id=run_id,
            channel="email",
        )
        increment_alerts_sent(alerts_sent)
        mark_polled(db, subscription)

        return PipelineResult(
            articles_fetched=len(raw_articles),
            articles_ranked=len(ranked),
            alerts_sent=alerts_sent,
        )
