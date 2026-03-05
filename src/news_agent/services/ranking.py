from __future__ import annotations

from datetime import datetime, timezone

from news_agent.config import get_settings
from news_agent.schemas import NormalizedArticle, RankedArticle
from news_agent.services.llm import LLMScorer

_SOURCE_TRUST = {
    "rss": 0.70,
    "hackernews": 0.75,
    "github": 0.65,
    "gnews": 0.80,
}


def _recency_score(published_at) -> float:
    hours_old = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
    return max(0.0, 1.0 - (hours_old / 24.0))


def _keyword_score(title: str, snippet: str, keywords: list[str]) -> float:
    haystack = f"{title} {snippet}".lower()
    if not keywords:
        return 0.2
    matches = sum(1 for keyword in keywords if keyword in haystack)
    return min(matches / max(len(keywords), 1), 1.0)


def _rule_reason(source_id: str, keyword_score: float, recency_score: float) -> str:
    return (
        f"source={source_id}, keyword_match={keyword_score:.2f}, recency={recency_score:.2f}"
    )


def rank_articles(
    normalized_articles: list[NormalizedArticle],
    query_profile: dict[str, object],
    llm_scorer: LLMScorer | None = None,
) -> list[RankedArticle]:
    settings = get_settings()
    keywords = [str(k).lower() for k in query_profile.get("keywords", [])]

    ranked: list[RankedArticle] = []
    for article in normalized_articles:
        k_score = _keyword_score(article.title, article.snippet, keywords)
        r_score = _recency_score(article.published_at)
        s_score = _SOURCE_TRUST.get(article.source_id, 0.5)
        q_score = article.quality_score

        rule_score = (0.40 * k_score) + (0.30 * r_score) + (0.20 * s_score) + (0.10 * q_score)
        ranked.append(
            RankedArticle(
                **article.model_dump(),
                rule_score=round(rule_score, 4),
                llm_score=0.0,
                final_score=round(rule_score, 4),
                reason=_rule_reason(article.source_id, k_score, r_score),
            )
        )

    ranked.sort(key=lambda x: x.rule_score, reverse=True)
    if not ranked:
        return ranked

    scorer = llm_scorer or LLMScorer()
    llm_candidates = ranked[: settings.llm_top_candidates]
    llm_scores = scorer.score_articles(llm_candidates, str(query_profile.get("interests", "")))

    for item in ranked:
        llm_score, llm_reason = llm_scores.get(item.fingerprint, (0.0, ""))
        item.llm_score = llm_score
        item.final_score = round((0.7 * item.rule_score) + (0.3 * llm_score), 4)
        if llm_reason:
            item.reason = f"{item.reason}; llm={llm_reason}"

    ranked.sort(key=lambda x: x.final_score, reverse=True)
    return ranked
