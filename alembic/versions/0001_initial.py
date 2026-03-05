"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-05 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("interests", sa.Text(), nullable=False),
        sa.Column("regions", sa.JSON(), nullable=False),
        sa.Column("languages", sa.JSON(), nullable=False),
        sa.Column("alert_frequency", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_alert_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_polled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_subscriptions_email", "subscriptions", ["email"], unique=True)

    op.create_table(
        "articles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=1024), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("lang", sa.String(length=32), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_articles_source_id", "articles", ["source_id"], unique=False)
    op.create_index("ix_articles_fingerprint", "articles", ["fingerprint"], unique=False)
    op.create_index("ix_articles_published_at", "articles", ["published_at"], unique=False)
    op.create_index("ix_articles_canonical_url", "articles", ["canonical_url"], unique=True)

    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("subscription_id", sa.String(length=36), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("articles_fetched", sa.Integer(), nullable=False),
        sa.Column("articles_ranked", sa.Integer(), nullable=False),
        sa.Column("alerts_sent", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("ix_pipeline_runs_subscription_id", "pipeline_runs", ["subscription_id"], unique=False)

    op.create_table(
        "alert_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("subscription_id", sa.String(length=36), sa.ForeignKey("subscriptions.id"), nullable=False),
        sa.Column("article_id", sa.String(length=36), sa.ForeignKey("articles.id"), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_id", sa.String(length=255), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "subscription_id",
            "article_id",
            "channel",
            name="uq_alert_per_article_channel",
        ),
    )
    op.create_index("ix_alert_events_subscription_id", "alert_events", ["subscription_id"], unique=False)
    op.create_index("ix_alert_events_status", "alert_events", ["status"], unique=False)
    op.create_index("ix_alert_events_run_id", "alert_events", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_alert_events_run_id", table_name="alert_events")
    op.drop_index("ix_alert_events_status", table_name="alert_events")
    op.drop_index("ix_alert_events_subscription_id", table_name="alert_events")
    op.drop_table("alert_events")

    op.drop_index("ix_pipeline_runs_subscription_id", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")

    op.drop_index("ix_articles_canonical_url", table_name="articles")
    op.drop_index("ix_articles_published_at", table_name="articles")
    op.drop_index("ix_articles_fingerprint", table_name="articles")
    op.drop_index("ix_articles_source_id", table_name="articles")
    op.drop_table("articles")

    op.drop_index("ix_subscriptions_email", table_name="subscriptions")
    op.drop_table("subscriptions")
