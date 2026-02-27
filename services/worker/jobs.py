from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import feedparser
import requests
from bs4 import BeautifulSoup
from rq import get_current_job
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

from core import ChunkDAO, DocumentDAO, get_session_factory, init_db

LOGGER = logging.getLogger(__name__)
disable_warnings(InsecureRequestWarning)
HTTP_HEADERS = {
    "User-Agent": "NarrativeIntelligenceEngine/1.0 (+https://localhost)",
    "Accept": "application/rss+xml, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
}


def _log(event: str, job_id: str, **extra: object) -> None:
    payload = {"event": event, "job_id": job_id, **extra}
    LOGGER.info(json.dumps(payload, ensure_ascii=True))


def _normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _compute_hash(url: str, title: str, normalized_text: str) -> str:
    base = f"{url.strip()}|{title.strip()}|{normalized_text}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _extract_html_text(url: str, timeout_seconds: int = 20, verify_ssl: bool = True) -> str:
    response = requests.get(url, timeout=timeout_seconds, verify=verify_ssl, headers=HTTP_HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    return soup.get_text(separator=" ", strip=True)


def _chunk_text(text: str, min_size: int = 800, max_size: int = 1200) -> list[str]:
    clean = _normalize_text(text)
    if not clean:
        return []

    words = clean.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        additional = len(word) + (1 if current else 0)
        if current and current_len + additional > max_size:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
            continue
        current.append(word)
        current_len += additional

    if current:
        chunks.append(" ".join(current))

    if len(chunks) > 1 and len(chunks[-1]) < min_size:
        chunks[-2] = f"{chunks[-2]} {chunks[-1]}".strip()
        chunks.pop()

    return chunks


def _parse_published_at(entry: feedparser.FeedParserDict) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed is None:
        return None
    return datetime(*parsed[:6], tzinfo=timezone.utc)


def _parse_feed(feed_url: str, timeout_seconds: int = 20, verify_ssl: bool = True):
    response = requests.get(feed_url, timeout=timeout_seconds, verify=verify_ssl, headers=HTTP_HEADERS)
    response.raise_for_status()
    return feedparser.parse(response.content)


def ingest_rss() -> dict[str, object]:
    job = get_current_job()
    job_id = job.id if job else f"local-{int(time.time())}"

    feeds_env = os.getenv("RSS_FEEDS", "")
    feed_urls = [item.strip() for item in feeds_env.split(",") if item.strip()]
    if not feed_urls:
        _log("ingest_empty_feed_list", job_id)
        return {
            "job_id": job_id,
            "processed": 0,
            "inserted": 0,
            "duplicates": 0,
            "chunks": 0,
            "feed_stats": [],
        }

    init_db()
    session_factory = get_session_factory()
    rate_limit_seconds = float(os.getenv("RSS_DOMAIN_SLEEP", "0.5"))
    verify_ssl = os.getenv("RSS_INSECURE_SSL", "true").lower() not in {"1", "true", "yes", "on"}
    last_seen_domain: dict[str, float] = {}

    processed = 0
    inserted = 0
    duplicates = 0
    created_chunks = 0
    feed_stats: list[dict[str, object]] = []

    with session_factory() as session:
        documents = DocumentDAO(session)
        chunks = ChunkDAO(session)

        for feed_url in feed_urls:
            try:
                feed = _parse_feed(feed_url, verify_ssl=verify_ssl)
            except Exception as exc:
                _log("feed_parse_failed", job_id, feed_url=feed_url, error=str(exc))
                feed_stats.append(
                    {
                        "feed_url": feed_url,
                        "source": "rss",
                        "entries": 0,
                        "processed": 0,
                        "inserted": 0,
                        "duplicates": 0,
                        "failed_fetch": 0,
                        "empty_or_skipped": 0,
                        "feed_error": str(exc),
                    }
                )
                continue
            entries = feed.entries or []
            _log("feed_loaded", job_id, feed_url=feed_url, entries=len(entries))
            feed_inserted = 0
            feed_duplicates = 0
            feed_failed = 0
            feed_empty = 0
            feed_processed = 0
            feed_source = feed.feed.get("title", "rss")

            for entry in entries:
                url = (entry.get("link") or "").strip()
                title = (entry.get("title") or "").strip() or "untitled"
                if not url:
                    feed_empty += 1
                    continue

                domain = urlparse(url).netloc
                now = time.time()
                if domain in last_seen_domain:
                    elapsed = now - last_seen_domain[domain]
                    wait_for = rate_limit_seconds - elapsed
                    if wait_for > 0:
                        time.sleep(wait_for)
                last_seen_domain[domain] = time.time()

                try:
                    raw_text = _extract_html_text(url, verify_ssl=verify_ssl)
                except Exception as exc:
                    _log("item_fetch_failed", job_id, url=url, error=str(exc))
                    feed_failed += 1
                    continue

                normalized_text = _normalize_text(raw_text)
                if not normalized_text:
                    feed_empty += 1
                    continue

                hash_value = _compute_hash(url, title, normalized_text)
                if documents.get_by_hash(hash_value) is not None:
                    duplicates += 1
                    processed += 1
                    feed_duplicates += 1
                    feed_processed += 1
                    continue

                doc = documents.create(
                    source=feed_source,
                    url=url,
                    title=title,
                    published_at=_parse_published_at(entry),
                    hash_value=hash_value,
                    raw_text=normalized_text,
                )
                chunk_rows = chunks.create_for_document(doc.id, _chunk_text(normalized_text))
                inserted += 1
                created_chunks += len(chunk_rows)
                processed += 1
                feed_inserted += 1
                feed_processed += 1

            feed_stat = {
                "feed_url": feed_url,
                "source": feed_source,
                "entries": len(entries),
                "processed": feed_processed,
                "inserted": feed_inserted,
                "duplicates": feed_duplicates,
                "failed_fetch": feed_failed,
                "empty_or_skipped": feed_empty,
            }
            feed_stats.append(feed_stat)
            _log("feed_summary", job_id, **feed_stat)

        session.commit()

    _log(
        "ingest_finished",
        job_id,
        processed=processed,
        inserted=inserted,
        duplicates=duplicates,
        chunks=created_chunks,
        feed_stats=feed_stats,
    )
    return {
        "job_id": job_id,
        "processed": processed,
        "inserted": inserted,
        "duplicates": duplicates,
        "chunks": created_chunks,
        "feed_stats": feed_stats,
    }
