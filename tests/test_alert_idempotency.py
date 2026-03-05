from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from news_agent.models import AlertEvent, Article, Subscription
from news_agent.schemas import RankedArticle
from news_agent.services.alerting import EmailAlertService


def test_same_article_not_sent_twice(db_session):
    sub = Subscription(
        email="alert@example.com",
        interests="ai",
        regions=["us"],
        languages=["en"],
        alert_frequency=15,
    )
    db_session.add(sub)
    db_session.commit()
    db_session.refresh(sub)

    article = Article(
        source_id="rss",
        title="AI News",
        url="https://example.com/1",
        canonical_url="https://example.com/1",
        published_at=datetime.now(timezone.utc),
        snippet="summary",
        author="",
        tags=["ai"],
        fingerprint="fp-article",
        lang="en",
        quality_score=0.8,
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)

    ranked = RankedArticle(
        source_id=article.source_id,
        title=article.title,
        url=article.url,
        published_at=article.published_at,
        snippet=article.snippet,
        author=article.author,
        tags=article.tags,
        canonical_url=article.canonical_url,
        fingerprint=article.fingerprint,
        lang=article.lang,
        quality_score=article.quality_score,
        rule_score=0.9,
        llm_score=0.0,
        final_score=0.9,
        reason="test",
    )

    service = EmailAlertService()
    first = service.send_alerts(
        db=db_session,
        subscription=sub,
        ranked_articles=[ranked],
        stored_articles={article.canonical_url: article},
        run_id="run-1",
    )
    second = service.send_alerts(
        db=db_session,
        subscription=sub,
        ranked_articles=[ranked],
        stored_articles={article.canonical_url: article},
        run_id="run-2",
    )

    sent_events = db_session.execute(
        select(AlertEvent).where(
            AlertEvent.subscription_id == sub.id,
            AlertEvent.article_id == article.id,
            AlertEvent.status == "sent",
        )
    ).scalars()

    assert first == 1
    assert second == 0
    assert len(list(sent_events)) == 1
