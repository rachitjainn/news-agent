from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser

from news_agent.schemas import RawArticle
from news_agent.sources.base import SourceAdapter


DEFAULT_FEEDS = [
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.theverge.com/rss/index.xml",
]


class RSSSource(SourceAdapter):
    name = "rss"

    def __init__(self, feeds: list[str] | None = None) -> None:
        super().__init__(timeout_seconds=12)
        self.feeds = feeds or DEFAULT_FEEDS

    def fetch(self, since_ts: datetime, query_profile: dict[str, object]) -> list[RawArticle]:
        articles: list[RawArticle] = []

        for feed_url in self.feeds:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries:
                raw_published = entry.get("published") or entry.get("updated")
                if raw_published:
                    try:
                        published_at = parsedate_to_datetime(raw_published)
                        if published_at.tzinfo is None:
                            published_at = published_at.replace(tzinfo=timezone.utc)
                    except Exception:  # noqa: BLE001
                        published_at = datetime.now(timezone.utc)
                else:
                    published_at = datetime.now(timezone.utc)

                if published_at < since_ts:
                    continue

                url = entry.get("link")
                title = entry.get("title", "")
                if not url or not title:
                    continue

                articles.append(
                    RawArticle(
                        source_id=self.name,
                        title=title,
                        url=url,
                        published_at=published_at,
                        snippet=entry.get("summary", ""),
                        author=entry.get("author", ""),
                        tags=[tag.get("term", "") for tag in entry.get("tags", []) if tag.get("term")],
                    )
                )

        return articles
