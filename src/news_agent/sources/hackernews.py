from __future__ import annotations

from datetime import datetime, timezone

from news_agent.schemas import RawArticle
from news_agent.sources.base import SourceAdapter


class HackerNewsSource(SourceAdapter):
    name = "hackernews"
    _base_url = "https://hacker-news.firebaseio.com/v0"

    def fetch(self, since_ts: datetime, query_profile: dict[str, object]) -> list[RawArticle]:
        stories: list[RawArticle] = []
        top_ids_payload = self._request_json(f"{self._base_url}/topstories.json")

        story_ids: list[int] = []
        if isinstance(top_ids_payload, list):
            story_ids = top_ids_payload[:50]
        elif isinstance(top_ids_payload, dict):
            # Defensive fallback if proxy wraps list in dict.
            maybe_ids = top_ids_payload.get("items", [])
            if isinstance(maybe_ids, list):
                story_ids = maybe_ids[:50]

        for story_id in story_ids:
            item = self._request_json(f"{self._base_url}/item/{story_id}.json")
            if not item:
                continue
            ts = item.get("time")
            if not isinstance(ts, int):
                continue
            published_at = datetime.fromtimestamp(ts, tz=timezone.utc)
            if published_at < since_ts:
                continue

            title = str(item.get("title", ""))
            url = str(item.get("url", "https://news.ycombinator.com/item?id=%s" % story_id))
            if not title:
                continue

            stories.append(
                RawArticle(
                    source_id=self.name,
                    title=title,
                    url=url,
                    published_at=published_at,
                    snippet=str(item.get("text", ""))[:600],
                    author=str(item.get("by", "")),
                    tags=["hackernews"],
                )
            )

        return stories
