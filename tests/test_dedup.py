from __future__ import annotations

from datetime import datetime, timezone

from news_agent.schemas import RawArticle
from news_agent.services.normalize import canonicalize_url, normalize_articles


def test_canonicalize_url_removes_tracking_params():
    url = "https://example.com/story/?utm_source=foo&fbclid=bar&id=7"
    canonical = canonicalize_url(url)
    assert canonical == "https://example.com/story?id=7"


def test_normalize_articles_deduplicates_by_fingerprint():
    now = datetime.now(timezone.utc)
    raw = [
        RawArticle(
            source_id="rss",
            title="Same Story",
            url="https://example.com/a?utm_campaign=123",
            published_at=now,
            snippet="one",
            author="",
            tags=[],
        ),
        RawArticle(
            source_id="rss",
            title="Same Story",
            url="https://example.com/a",
            published_at=now,
            snippet="two",
            author="",
            tags=[],
        ),
    ]

    normalized = normalize_articles(raw)
    assert len(normalized) == 1
