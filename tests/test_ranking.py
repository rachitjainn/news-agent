from __future__ import annotations

from datetime import datetime, timedelta, timezone

from news_agent.schemas import NormalizedArticle
from news_agent.services.ranking import rank_articles


def test_rank_articles_prefers_keyword_match_and_recency():
    now = datetime.now(timezone.utc)
    target = NormalizedArticle(
        source_id="rss",
        title="AI startup launches coding model",
        url="https://example.com/ai",
        canonical_url="https://example.com/ai",
        published_at=now,
        snippet="new model for developers",
        author="",
        tags=["ai"],
        fingerprint="fp-target",
        lang="en",
        quality_score=0.9,
    )

    older = NormalizedArticle(
        source_id="rss",
        title="Sports update",
        url="https://example.com/sports",
        canonical_url="https://example.com/sports",
        published_at=now - timedelta(hours=20),
        snippet="match results",
        author="",
        tags=["sports"],
        fingerprint="fp-old",
        lang="en",
        quality_score=0.5,
    )

    ranked = rank_articles(
        [older, target],
        query_profile={"interests": "ai developer tools", "keywords": ["ai", "developer", "tools"]},
    )

    assert ranked[0].fingerprint == "fp-target"
    assert ranked[0].final_score >= ranked[1].final_score
