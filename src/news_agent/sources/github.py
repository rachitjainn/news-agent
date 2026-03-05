from __future__ import annotations

from datetime import datetime, timedelta, timezone

from news_agent.config import get_settings
from news_agent.schemas import RawArticle
from news_agent.sources.base import SourceAdapter


class GitHubSource(SourceAdapter):
    name = "github"

    def fetch(self, since_ts: datetime, query_profile: dict[str, object]) -> list[RawArticle]:
        settings = get_settings()
        created_since = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        headers: dict[str, str] = {}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
            headers["Accept"] = "application/vnd.github+json"
        payload = self._request_json(
            "https://api.github.com/search/repositories",
            params={
                "q": f"created:>={created_since}",
                "sort": "stars",
                "order": "desc",
                "per_page": 30,
            },
            headers=headers,
        )

        items = payload.get("items", []) if isinstance(payload, dict) else []
        if not isinstance(items, list):
            return []

        articles: list[RawArticle] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            created_at_raw = item.get("created_at")
            try:
                published_at = datetime.fromisoformat(str(created_at_raw).replace("Z", "+00:00"))
            except Exception:  # noqa: BLE001
                published_at = datetime.now(timezone.utc)
            if published_at < since_ts:
                continue

            repo_url = str(item.get("html_url", ""))
            full_name = str(item.get("full_name", ""))
            if not repo_url or not full_name:
                continue

            articles.append(
                RawArticle(
                    source_id=self.name,
                    title=f"Trending repo: {full_name}",
                    url=repo_url,
                    published_at=published_at,
                    snippet=str(item.get("description", "")),
                    author=str(item.get("owner", {}).get("login", "")),
                    tags=[str(item.get("language", "")).lower()] if item.get("language") else [],
                )
            )

        return articles
