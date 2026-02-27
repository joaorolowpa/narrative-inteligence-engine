from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DEFAULT_DB_URL = "sqlite:///./data/app.db"

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _ensure_sqlite_path(db_url: str) -> None:
    if not db_url.startswith("sqlite:///"):
        return
    raw_path = db_url.replace("sqlite:///", "", 1)
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)


def _configure_wal(engine: Engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()


def init_db(db_url: str | None = None) -> None:
    global _engine, _session_factory

    resolved_url = db_url or os.getenv("DATABASE_URL", DEFAULT_DB_URL)
    _ensure_sqlite_path(resolved_url)

    if _engine is None or str(_engine.url) != resolved_url:
        _engine = create_engine(resolved_url, future=True)
        _configure_wal(_engine)
        _session_factory = sessionmaker(bind=_engine, expire_on_commit=False, class_=Session)
        Base.metadata.create_all(_engine)

    if str(_engine.url).startswith("sqlite"):
        with _engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL;"))


def get_engine() -> Engine:
    if _engine is None:
        init_db()
    assert _engine is not None
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    if _session_factory is None:
        init_db()
    assert _session_factory is not None
    return _session_factory
