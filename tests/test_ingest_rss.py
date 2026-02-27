from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import select, text

from core import DocumentDAO, get_engine, get_session_factory, init_db
from core.models import Chunk
from services.worker import jobs


def test_ingest_rss_dedup_chunking_and_persistence(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'app.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("RSS_FEEDS", "https://example.com/feed.xml")
    monkeypatch.setenv("RSS_DOMAIN_SLEEP", "0")

    def fake_feed_parse(_url: str):
        return SimpleNamespace(
            feed={"title": "Example Feed"},
            entries=[
                {
                    "link": "https://example.com/post-1",
                    "title": "Post 1",
                }
            ],
        )

    large_text = " ".join(["texto"] * 700)

    monkeypatch.setattr(jobs.feedparser, "parse", fake_feed_parse)
    monkeypatch.setattr(jobs, "_extract_html_text", lambda _url: large_text)

    first = jobs.ingest_rss()
    second = jobs.ingest_rss()

    assert first["inserted"] == 1
    assert second["inserted"] == 0
    assert second["duplicates"] == 1

    session_factory = get_session_factory()
    with session_factory() as session:
        docs = DocumentDAO(session).list_latest(50)
        chunk_rows = list(session.execute(select(Chunk)).scalars().all())

    assert len(docs) == 1
    assert len(chunk_rows) >= 2
    assert 800 <= len(chunk_rows[0].text) <= 1200


def test_sqlite_wal_is_enabled(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'wal.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    init_db(db_url)

    engine = get_engine()
    with engine.connect() as conn:
        mode = conn.execute(text("PRAGMA journal_mode;")).scalar_one()

    assert str(mode).lower() == "wal"
