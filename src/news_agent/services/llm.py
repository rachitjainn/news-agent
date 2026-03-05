from __future__ import annotations

import json

from openai import OpenAI

from news_agent.config import get_settings
from news_agent.logging import get_logger
from news_agent.schemas import RankedArticle

logger = get_logger(__name__)


class LLMScorer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.enabled = bool(self.settings.enable_llm and self.settings.openai_api_key)
        self.client: OpenAI | None = None
        if self.enabled:
            self.client = OpenAI(api_key=self.settings.openai_api_key)

    def score_articles(
        self,
        articles: list[RankedArticle],
        interests: str,
    ) -> dict[str, tuple[float, str]]:
        if not self.enabled or not self.client or not articles:
            return {}

        prompt_items = [
            {
                "fingerprint": a.fingerprint,
                "title": a.title,
                "snippet": a.snippet,
                "source_id": a.source_id,
            }
            for a in articles
        ]

        prompt = {
            "task": "Score relevance for personalized alerts from 0 to 1 and return concise reasons.",
            "interests": interests,
            "articles": prompt_items,
            "output_schema": {
                "scores": [
                    {
                        "fingerprint": "string",
                        "llm_score": "float_between_0_and_1",
                        "reason": "short string",
                    }
                ]
            },
        }

        try:
            response = self.client.responses.create(
                model=self.settings.openai_model,
                input=[
                    {
                        "role": "system",
                        "content": "You are a ranking model. Return strict JSON only.",
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                temperature=0.0,
            )
            text = response.output_text
            payload = json.loads(text)
            scored = {}
            for item in payload.get("scores", []):
                fp = item.get("fingerprint")
                if not fp:
                    continue
                llm_score = float(item.get("llm_score", 0.0))
                reason = str(item.get("reason", ""))
                scored[str(fp)] = (max(0.0, min(llm_score, 1.0)), reason)
            return scored
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_scoring_failed", error=str(exc))
            return {}
