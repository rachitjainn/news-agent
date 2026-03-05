from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="news-agent", alias="APP_NAME")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/news_agent",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    queue_name: str = Field(default="news-jobs", alias="QUEUE_NAME")

    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    from_email: str = Field(default="news-agent@example.com", alias="FROM_EMAIL")

    poll_interval_minutes: int = Field(default=5, alias="POLL_INTERVAL_MINUTES")
    alert_debounce_minutes: int = Field(default=15, alias="ALERT_DEBOUNCE_MINUTES")
    max_alert_articles: int = Field(default=8, alias="MAX_ALERT_ARTICLES")
    max_fetch_articles: int = Field(default=50, alias="MAX_FETCH_ARTICLES")

    gnews_api_key: str = Field(default="", alias="GNEWS_API_KEY")
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    llm_top_candidates: int = Field(default=10, alias="LLM_TOP_CANDIDATES")
    enable_llm: bool = Field(default=True, alias="ENABLE_LLM")
    enable_digest_fallback: bool = Field(default=True, alias="ENABLE_DIGEST_FALLBACK")

    worker_heartbeat_ttl_seconds: int = Field(default=180, alias="WORKER_HEARTBEAT_TTL_SECONDS")
    scheduler_heartbeat_ttl_seconds: int = Field(
        default=180,
        alias="SCHEDULER_HEARTBEAT_TTL_SECONDS",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
