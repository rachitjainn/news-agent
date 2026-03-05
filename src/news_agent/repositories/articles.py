from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from news_agent.models import Article
from news_agent.schemas import NormalizedArticle


def find_existing_fingerprints(
    db: Session,
    fingerprints: list[str],
    window_hours: int = 24,
) -> set[str]:
    if not fingerprints:
        return set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    rows = db.execute(
        select(Article.fingerprint).where(
            Article.fingerprint.in_(fingerprints),
            Article.published_at >= cutoff,
        )
    )
    return {row[0] for row in rows}


def upsert_articles(db: Session, normalized_articles: list[NormalizedArticle]) -> list[Article]:
    if not normalized_articles:
        return []

    canonical_urls = [article.canonical_url for article in normalized_articles]
    existing_rows = db.execute(
        select(Article).where(Article.canonical_url.in_(canonical_urls))
    ).scalars()
    existing_map = {row.canonical_url: row for row in existing_rows}

    stored: list[Article] = []
    for item in normalized_articles:
        current = existing_map.get(item.canonical_url)
        if current is None:
            current = Article(
                source_id=item.source_id,
                title=item.title,
                url=item.url,
                canonical_url=item.canonical_url,
                published_at=item.published_at,
                snippet=item.snippet,
                author=item.author,
                tags=item.tags,
                fingerprint=item.fingerprint,
                lang=item.lang,
                quality_score=item.quality_score,
            )
            db.add(current)
            existing_map[item.canonical_url] = current
        else:
            current.title = item.title
            current.url = item.url
            current.published_at = item.published_at
            current.snippet = item.snippet
            current.author = item.author
            current.tags = item.tags
            current.fingerprint = item.fingerprint
            current.lang = item.lang
            current.quality_score = item.quality_score
        stored.append(current)

    db.commit()
    for article in stored:
        db.refresh(article)
    return stored
