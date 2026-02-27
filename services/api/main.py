from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from redis import Redis
from rq import Queue

from core import DocumentDAO, get_session_factory, init_db
from core.schemas import (
    ClearDocumentsResponse,
    DocumentResponse,
    HealthResponse,
    JobEnqueueResponse,
)

app = FastAPI(title="Narrative Intelligence API")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/jobs/ingest", response_model=JobEnqueueResponse)
def enqueue_ingest(sync: bool = False) -> JobEnqueueResponse:
    if sync:
        from services.worker.jobs import ingest_rss

        result = ingest_rss()
        return JobEnqueueResponse(job_id=str(result["job_id"]), status="completed")

    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    try:
        conn = Redis.from_url(redis_url)
        queue = Queue("default", connection=conn)
        job = queue.enqueue("services.worker.jobs.ingest_rss")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not enqueue ingest job: {exc}") from exc

    return JobEnqueueResponse(job_id=job.id, status="queued")


@app.get("/documents", response_model=list[DocumentResponse])
def list_documents() -> list[DocumentResponse]:
    session_factory = get_session_factory()
    with session_factory() as session:
        items = DocumentDAO(session).list_latest(limit=50)
        return [
            DocumentResponse(
                id=item.id,
                source=item.source,
                url=item.url,
                title=item.title,
                published_at=item.published_at,
                hash=item.hash,
                raw_text=item.raw_text,
                created_at=item.created_at,
            )
            for item in items
        ]


@app.get("/documents/latest", response_model=DocumentResponse)
def get_latest_document() -> DocumentResponse:
    session_factory = get_session_factory()
    with session_factory() as session:
        item = DocumentDAO(session).get_latest()
        if item is None:
            raise HTTPException(status_code=404, detail="No documents found")
        return DocumentResponse(
            id=item.id,
            source=item.source,
            url=item.url,
            title=item.title,
            published_at=item.published_at,
            hash=item.hash,
            raw_text=item.raw_text,
            created_at=item.created_at,
        )


@app.delete("/documents", response_model=ClearDocumentsResponse)
def clear_documents() -> ClearDocumentsResponse:
    session_factory = get_session_factory()
    with session_factory() as session:
        deleted_documents, deleted_chunks = DocumentDAO(session).clear_all()
        session.commit()
        return ClearDocumentsResponse(
            deleted_documents=deleted_documents,
            deleted_chunks=deleted_chunks,
        )
