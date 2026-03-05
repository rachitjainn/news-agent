from __future__ import annotations

from datetime import datetime, timezone

from news_agent.models import AlertEvent, Article, Subscription


class FakeQueue:
    def __init__(self):
        self.calls = []

    def enqueue(self, *args, **kwargs):  # noqa: ANN002, ANN003
        self.calls.append((args, kwargs))
        return {"id": "job-1"}


def test_subscription_crud_and_run_now(client, db_session, monkeypatch):
    create_payload = {
        "email": "user@example.com",
        "interests": "AI startups and developer tools",
        "regions": ["us"],
        "languages": ["en"],
        "alert_frequency": 15,
    }

    create_resp = client.post("/v1/subscriptions", json=create_payload)
    assert create_resp.status_code == 201
    sub_id = create_resp.json()["subscription_id"]

    patch_resp = client.patch(
        f"/v1/subscriptions/{sub_id}",
        json={"interests": "AI and open source", "alert_frequency": 30},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["alert_frequency"] == 30

    fake_queue = FakeQueue()
    monkeypatch.setattr("news_agent.api.routes.get_queue", lambda: fake_queue)

    run_resp = client.post(f"/v1/run-now/{sub_id}")
    assert run_resp.status_code == 200
    assert run_resp.json()["queued"] is True
    assert len(fake_queue.calls) == 1

    delete_resp = client.delete(f"/v1/subscriptions/{sub_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "deleted"


def test_alert_history(client, db_session):
    subscription = Subscription(
        email="history@example.com",
        interests="ai",
        regions=["us"],
        languages=["en"],
        alert_frequency=15,
    )
    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)

    article = Article(
        source_id="rss",
        title="AI headline",
        url="https://example.com/a",
        canonical_url="https://example.com/a",
        published_at=datetime.now(timezone.utc),
        snippet="snippet",
        author="author",
        tags=["ai"],
        fingerprint="fp-1",
        lang="en",
        quality_score=0.9,
    )
    db_session.add(article)
    db_session.commit()
    db_session.refresh(article)

    event = AlertEvent(
        subscription_id=subscription.id,
        article_id=article.id,
        channel="email",
        status="sent",
        sent_at=datetime.now(timezone.utc),
    )
    db_session.add(event)
    db_session.commit()

    response = client.get(f"/v1/alerts/history?subscription_id={subscription.id}&page=1&page_size=10")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["status"] == "sent"


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["api"] == "ok"
    assert body["db"] == "up"
