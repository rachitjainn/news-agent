from __future__ import annotations

import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from uuid import uuid4

from sqlalchemy.orm import Session

from news_agent.config import get_settings
from news_agent.logging import get_logger
from news_agent.models import Article, Subscription
from news_agent.repositories.alerts import create_alert_event
from news_agent.repositories.subscriptions import mark_alert_sent
from news_agent.schemas import RankedArticle

logger = get_logger(__name__)


class EmailAlertService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _debounce_window_minutes(self, subscription: Subscription) -> int:
        return max(subscription.alert_frequency, self.settings.alert_debounce_minutes)

    def _is_debounced(self, subscription: Subscription, now: datetime) -> bool:
        if subscription.last_alert_sent_at is None:
            return False
        window = timedelta(minutes=self._debounce_window_minutes(subscription))
        return (now - subscription.last_alert_sent_at) < window

    def _render_email(self, subscription: Subscription, articles: list[RankedArticle]) -> tuple[str, str]:
        subject = f"News Alert: {len(articles)} updates for your interests"
        list_items = "\n".join(
            (
                f"<li><a href=\"{a.url}\">{a.title}</a>"
                f"<br/><small>Score {a.final_score:.2f} | {a.source_id}</small>"
                f"<p>{a.snippet[:240]}</p></li>"
            )
            for a in articles
        )
        body = (
            f"<h2>Hi, here are your latest news matches</h2>"
            f"<p>Interests: {subscription.interests}</p>"
            f"<ul>{list_items}</ul>"
        )
        return subject, body

    def _smtp_send(self, to_email: str, subject: str, html_body: str) -> str:
        if not self.settings.smtp_host:
            logger.info("email_dry_run", to_email=to_email, subject=subject)
            return "dry-run"

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.settings.from_email
        message["To"] = to_email
        message.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.sendmail(self.settings.from_email, [to_email], message.as_string())

        return "smtp"

    def _enqueue_digest_fallback(self, subscription: Subscription, run_id: str) -> None:
        if not self.settings.enable_digest_fallback:
            return

        wait_minutes = self._debounce_window_minutes(subscription)
        if wait_minutes <= 0:
            return

        try:
            from news_agent.jobs import process_subscription_job
            from news_agent.queue import get_queue, get_redis_connection

            redis_conn = get_redis_connection()
            lock_key = f"news_agent:digest-fallback:{subscription.id}"
            if redis_conn.setnx(lock_key, run_id):
                redis_conn.expire(lock_key, int(wait_minutes * 60))
                get_queue().enqueue_in(
                    timedelta(minutes=wait_minutes),
                    process_subscription_job,
                    subscription.id,
                    str(uuid4()),
                    job_timeout=600,
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "digest_fallback_enqueue_failed",
                subscription_id=subscription.id,
                error=str(exc),
            )

    def send_alerts(
        self,
        db: Session,
        subscription: Subscription,
        ranked_articles: list[RankedArticle],
        stored_articles: dict[str, Article],
        run_id: str,
        channel: str = "email",
    ) -> int:
        if not ranked_articles:
            return 0

        now = datetime.now(timezone.utc)
        selected = ranked_articles[: self.settings.max_alert_articles]
        selected_articles = [stored_articles[a.canonical_url] for a in selected if a.canonical_url in stored_articles]
        if not selected_articles:
            return 0

        if self._is_debounced(subscription, now):
            for article in selected_articles:
                create_alert_event(
                    db=db,
                    subscription_id=subscription.id,
                    article_id=article.id,
                    channel=channel,
                    status="debounced",
                    run_id=run_id,
                    sent_at=now,
                )
            self._enqueue_digest_fallback(subscription, run_id)
            return 0

        subject, body = self._render_email(subscription, selected)

        try:
            provider_id = self._smtp_send(subscription.email, subject, body)
            sent_count = 0
            for article in selected_articles:
                created = create_alert_event(
                    db=db,
                    subscription_id=subscription.id,
                    article_id=article.id,
                    channel=channel,
                    status="sent",
                    run_id=run_id,
                    provider_id=provider_id,
                    sent_at=now,
                )
                if created is not None:
                    sent_count += 1
            if sent_count > 0:
                mark_alert_sent(db, subscription)
            return sent_count
        except Exception as exc:  # noqa: BLE001
            logger.error("email_send_failed", subscription_id=subscription.id, error=str(exc))
            create_alert_event(
                db=db,
                subscription_id=subscription.id,
                article_id=None,
                channel=channel,
                status="failed",
                run_id=run_id,
                error=str(exc),
                sent_at=now,
            )
            return 0
