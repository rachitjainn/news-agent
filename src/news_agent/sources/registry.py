from news_agent.sources.base import SourceAdapter
from news_agent.sources.github import GitHubSource
from news_agent.sources.gnews import GNewsSource
from news_agent.sources.hackernews import HackerNewsSource
from news_agent.sources.rss import RSSSource


def build_source_registry() -> list[SourceAdapter]:
    return [
        RSSSource(),
        HackerNewsSource(),
        GitHubSource(),
        GNewsSource(),
    ]
