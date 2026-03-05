from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from news_agent.config import get_settings
from news_agent.models import Base

_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _create_engine(database_url: str) -> Engine:
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


def configure_engine(database_url: str | None = None) -> None:
    global _engine, SessionLocal
    settings = get_settings()
    target_url = database_url or settings.database_url
    _engine = _create_engine(target_url)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        configure_engine()
    assert _engine is not None
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global SessionLocal
    if SessionLocal is None:
        configure_engine()
    assert SessionLocal is not None
    return SessionLocal


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
