from __future__ import annotations

import hashlib
import re
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from news_agent.schemas import NormalizedArticle, RawArticle

_STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "you",
    "your",
    "into",
    "about",
    "news",
}


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    normalized_path = parsed.path or "/"
    if normalized_path != "/" and normalized_path.endswith("/"):
        normalized_path = normalized_path.rstrip("/")

    filtered_qs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in {"fbclid", "gclid", "mc_cid", "mc_eid"}:
            continue
        filtered_qs.append((key, value))

    canonical = parsed._replace(
        scheme=parsed.scheme.lower() or "https",
        netloc=parsed.netloc.lower(),
        path=normalized_path,
        query=urlencode(filtered_qs, doseq=True),
        fragment="",
    )
    normalized = urlunparse(canonical)
    return normalized.rstrip("/")


def normalize_title(title: str) -> str:
    lowered = title.lower()
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def compute_fingerprint(title: str, canonical_url: str) -> str:
    basis = f"{normalize_title(title)}|{canonical_url}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def estimate_language(article: RawArticle) -> str:
    text = f"{article.title} {article.snippet}".strip()
    if not text:
        return "unknown"
    ascii_ratio = sum(1 for ch in text if ord(ch) < 128) / max(len(text), 1)
    return "en" if ascii_ratio > 0.95 else "unknown"


def estimate_quality(source_id: str, snippet: str) -> float:
    source_bonus = {
        "rss": 0.6,
        "hackernews": 0.7,
        "github": 0.5,
        "gnews": 0.8,
    }.get(source_id, 0.4)
    snippet_bonus = min(len(snippet) / 400, 1.0) * 0.4
    return round(source_bonus + snippet_bonus, 3)


def normalize_articles(raw_articles: list[RawArticle]) -> list[NormalizedArticle]:
    out: list[NormalizedArticle] = []
    seen_fingerprints: set[str] = set()
    for article in raw_articles:
        canonical = canonicalize_url(article.url)
        fp = compute_fingerprint(article.title, canonical)
        if fp in seen_fingerprints:
            continue
        seen_fingerprints.add(fp)

        out.append(
            NormalizedArticle(
                **article.model_dump(),
                canonical_url=canonical,
                fingerprint=fp,
                lang=estimate_language(article),
                quality_score=estimate_quality(article.source_id, article.snippet),
            )
        )
    return out


def extract_keywords(interests: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9+#.-]+", interests.lower())
    cleaned = [t for t in tokens if len(t) > 2 and t not in _STOP_WORDS]

    # Keep order while de-duplicating.
    seen = set()
    keywords = []
    for token in cleaned:
        if token in seen:
            continue
        seen.add(token)
        keywords.append(token)
    return keywords[:20]


def build_query_profile(
    interests: str,
    regions: list[str],
    languages: list[str],
    now: datetime,
) -> dict[str, object]:
    return {
        "interests": interests,
        "keywords": extract_keywords(interests),
        "regions": regions,
        "languages": languages or ["en"],
        "requested_at": now.isoformat(),
    }
