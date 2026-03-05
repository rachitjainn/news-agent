from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def configured_env(monkeypatch: pytest.MonkeyPatch, tmp_path):
    db_path = tmp_path / "test.db"
    db_url = f"sqlite:///{db_path}"

    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/15")
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("ENABLE_LLM", "false")
    monkeypatch.setenv("ENABLE_DIGEST_FALLBACK", "false")

    from news_agent.config import get_settings
    from news_agent.db import configure_engine, init_db
    from news_agent.queue import get_queue, get_redis_connection

    get_settings.cache_clear()
    get_queue.cache_clear()
    get_redis_connection.cache_clear()

    configure_engine(db_url)
    init_db()

    return db_url


@pytest.fixture
def client(configured_env) -> Generator[TestClient, None, None]:
    from news_agent.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_session(configured_env):
    from news_agent.db import get_session_factory

    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
