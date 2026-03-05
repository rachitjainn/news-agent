from __future__ import annotations

from datetime import datetime, timezone

from news_agent.config import get_settings
from news_agent.schemas import RawArticle
from news_agent.sources.base import SourceAdapter


class GNewsSource(SourceAdapter):
    name = "gnews"

    def fetch(self, since_ts: datetime, query_profile: dict[str, object]) -> list[RawArticle]:
        settings = get_settings()
        if not settings.gnews_api_key:
            return []

        keywords = " OR ".join(query_profile.get("keywords", []))
        if not keywords:
            keywords = "technology"

        params = {
            "q": keywords,
            "lang": (query_profile.get("languages") or ["en"])[0],
            "apikey": settings.gnews_api_key,
            "max": min(settings.max_fetch_articles, 50),
        }
        payload = self._request_json("https://gnews.io/api/v4/search", params=params)
        raw_articles = payload.get("articles", []) if isinstance(payload, dict) else []
        if not isinstance(raw_articles, list):
            return []

        output: list[RawArticle] = []
        for item in raw_articles:
            if not isinstance(item, dict):
                continue
            try:
                published_at = datetime.fromisoformat(str(item.get("publishedAt", "")).replace("Z", "+00:00"))
            except Exception:  # noqa: BLE001
                published_at = datetime.now(timezone.utc)
            if published_at < since_ts:
                continue

            title = str(item.get("title", ""))
            url = str(item.get("url", ""))
            if not title or not url:
                continue

            output.append(
                RawArticle(
                    source_id=self.name,
                    title=title,
                    url=url,
                    published_at=published_at,
                    snippet=str(item.get("description", "")),
                    author=str(item.get("source", {}).get("name", "")),
                    tags=query_profile.get("keywords", [])[:3],
                )
            )

        return output
