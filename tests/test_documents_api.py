from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from services.api.main import app
from services.worker import jobs


def test_ingest_sync_and_list_documents(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'api.db'}"
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

    monkeypatch.setattr(jobs.feedparser, "parse", fake_feed_parse)
    monkeypatch.setattr(jobs, "_extract_html_text", lambda _url: "texto " * 300)

    client = TestClient(app)
    enqueue_response = client.post("/jobs/ingest?sync=true")
    docs_response = client.get("/documents")

    assert enqueue_response.status_code == 200
    assert enqueue_response.json()["status"] == "completed"

    assert docs_response.status_code == 200
    body = docs_response.json()
    assert len(body) == 1
    assert body[0]["title"] == "Post 1"


def test_get_latest_and_clear_documents(tmp_path, monkeypatch) -> None:
    db_url = f"sqlite:///{tmp_path / 'api2.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("RSS_FEEDS", "https://example.com/feed.xml")
    monkeypatch.setenv("RSS_DOMAIN_SLEEP", "0")

    def fake_feed_parse(_url: str):
        return SimpleNamespace(
            feed={"title": "Example Feed"},
            entries=[
                {
                    "link": "https://example.com/post-a",
                    "title": "Post A",
                },
                {
                    "link": "https://example.com/post-b",
                    "title": "Post B",
                },
            ],
        )

    monkeypatch.setattr(jobs.feedparser, "parse", fake_feed_parse)
    monkeypatch.setattr(jobs, "_extract_html_text", lambda _url: "texto " * 350)

    client = TestClient(app)
    ingest_response = client.post("/jobs/ingest?sync=true")
    latest_response = client.get("/documents/latest")
    clear_response = client.delete("/documents")
    after_clear_latest = client.get("/documents/latest")

    assert ingest_response.status_code == 200
    assert latest_response.status_code == 200
    assert latest_response.json()["title"] in {"Post A", "Post B"}

    assert clear_response.status_code == 200
    assert clear_response.json()["deleted_documents"] >= 1

    assert after_clear_latest.status_code == 404
