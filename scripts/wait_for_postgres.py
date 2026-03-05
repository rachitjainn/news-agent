#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import time

from sqlalchemy import create_engine, text


def main() -> int:
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/news_agent",
    )
    attempts = int(os.getenv("DB_WAIT_ATTEMPTS", "30"))
    sleep_seconds = float(os.getenv("DB_WAIT_INTERVAL_SECONDS", "1"))

    print(f"Waiting for Postgres at {database_url} ...")

    for attempt in range(1, attempts + 1):
        try:
            engine = create_engine(database_url, pool_pre_ping=True)
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print(f"Postgres is ready (attempt {attempt}/{attempts})")
            return 0
        except Exception as exc:  # noqa: BLE001
            print(f"Attempt {attempt}/{attempts} failed: {exc}")
            time.sleep(sleep_seconds)

    print("Postgres did not become ready in time.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
