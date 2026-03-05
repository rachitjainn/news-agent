from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime

import httpx

from news_agent.logging import get_logger
from news_agent.schemas import RawArticle

logger = get_logger(__name__)


class SourceAdapter(ABC):
    name: str

    def __init__(self, *, timeout_seconds: int = 10, max_retries: int = 2) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._consecutive_failures = 0
        self._opened_until: float = 0.0

    @abstractmethod
    def fetch(self, since_ts: datetime, query_profile: dict[str, object]) -> list[RawArticle]:
        """Fetch articles since timestamp for a subscription query profile."""

    def _circuit_is_open(self) -> bool:
        return time.time() < self._opened_until

    def _record_success(self) -> None:
        self._consecutive_failures = 0

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= 5:
            self._opened_until = time.time() + 60
            logger.warning("source_circuit_open", source=self.name, duration_seconds=60)

    def _request_json(
        self,
        url: str,
        params: dict[str, object] | None = None,
    ) -> dict[str, object] | list[object]:
        if self._circuit_is_open():
            logger.warning("source_skipped_circuit_open", source=self.name)
            return {}

        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    payload = response.json()
                self._record_success()
                if isinstance(payload, (dict, list)):
                    return payload
                return {}
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                sleep_seconds = 0.4 * (2**attempt)
                time.sleep(sleep_seconds)

        self._record_failure()
        logger.warning("source_request_failed", source=self.name, error=str(last_exc))
        return {}
