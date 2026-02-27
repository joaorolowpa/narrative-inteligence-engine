from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class JobEnqueueResponse(BaseModel):
    job_id: str
    status: str


class DocumentResponse(BaseModel):
    id: int
    source: str
    url: str
    title: str
    published_at: datetime | None
    hash: str
    raw_text: str
    created_at: datetime


class ClearDocumentsResponse(BaseModel):
    deleted_documents: int
    deleted_chunks: int
