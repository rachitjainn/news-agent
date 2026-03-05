from prometheus_client import Counter

articles_fetched_total = Counter(
    "news_agent_articles_fetched_total",
    "Total fetched articles by source",
    ["source"],
)
source_errors_total = Counter(
    "news_agent_source_errors_total",
    "Total source fetch errors",
    ["source"],
)
articles_ranked_total = Counter(
    "news_agent_articles_ranked_total",
    "Total ranked articles",
)
alerts_sent_total = Counter(
    "news_agent_alerts_sent_total",
    "Total alerts sent",
)


def increment_articles_fetched(source: str, count: int) -> None:
    if count > 0:
        articles_fetched_total.labels(source=source).inc(count)


def increment_source_error(source: str) -> None:
    source_errors_total.labels(source=source).inc()


def increment_articles_ranked(count: int) -> None:
    if count > 0:
        articles_ranked_total.inc(count)


def increment_alerts_sent(count: int) -> None:
    if count > 0:
        alerts_sent_total.inc(count)
