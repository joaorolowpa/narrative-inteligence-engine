from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .domain import Narrative
from .models import (
    Alert,
    Chunk,
    Document,
    NarrativeDoc,
    NarrativeExposure,
    NarrativeModel,
    PortfolioPosition,
)


class InMemoryNarrativeRepo:
    def __init__(self) -> None:
        self._items: dict[str, Narrative] = {}

    def save(self, narrative: Narrative) -> None:
        self._items[narrative.id] = narrative

    def get(self, narrative_id: str) -> Narrative | None:
        return self._items.get(narrative_id)


class DocumentDAO:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_hash(self, hash_value: str) -> Document | None:
        stmt = select(Document).where(Document.hash == hash_value)
        return self.session.execute(stmt).scalar_one_or_none()

    def create(
        self,
        *,
        source: str,
        url: str,
        title: str,
        published_at: datetime | None,
        hash_value: str,
        raw_text: str,
    ) -> Document:
        doc = Document(
            source=source,
            url=url,
            title=title,
            published_at=published_at,
            hash=hash_value,
            raw_text=raw_text,
        )
        self.session.add(doc)
        self.session.flush()
        return doc

    def list_latest(self, limit: int = 50) -> list[Document]:
        stmt = select(Document).order_by(Document.created_at.desc()).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def get_latest(self) -> Document | None:
        stmt = select(Document).order_by(Document.created_at.desc()).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def clear_all(self) -> tuple[int, int]:
        deleted_chunks = self.session.execute(delete(Chunk)).rowcount or 0
        deleted_documents = self.session.execute(delete(Document)).rowcount or 0
        self.session.flush()
        return deleted_documents, deleted_chunks


class ChunkDAO:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_for_document(self, document_id: int, chunks: Iterable[str]) -> list[Chunk]:
        rows: list[Chunk] = []
        for idx, chunk_text in enumerate(chunks):
            row = Chunk(document_id=document_id, chunk_index=idx, text=chunk_text)
            rows.append(row)
            self.session.add(row)
        self.session.flush()
        return rows


class NarrativeDAO:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        name: str,
        summary: str,
        momentum_score: float,
        window_start: datetime | None,
        window_end: datetime | None,
    ) -> NarrativeModel:
        narrative = NarrativeModel(
            name=name,
            summary=summary,
            momentum_score=momentum_score,
            window_start=window_start,
            window_end=window_end,
        )
        self.session.add(narrative)
        self.session.flush()
        return narrative


class NarrativeDocDAO:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, narrative_id: int, document_id: int, score: float) -> NarrativeDoc:
        row = NarrativeDoc(narrative_id=narrative_id, document_id=document_id, score=score)
        self.session.add(row)
        self.session.flush()
        return row


class PortfolioPositionDAO:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, portfolio_id: str, ticker: str, weight: float) -> PortfolioPosition:
        row = PortfolioPosition(portfolio_id=portfolio_id, ticker=ticker, weight=weight)
        self.session.add(row)
        self.session.flush()
        return row


class NarrativeExposureDAO:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self, *, narrative_id: int, ticker: str, exposure_score: float, rationale: str
    ) -> NarrativeExposure:
        row = NarrativeExposure(
            narrative_id=narrative_id,
            ticker=ticker,
            exposure_score=exposure_score,
            rationale=rationale,
        )
        self.session.add(row)
        self.session.flush()
        return row


class AlertDAO:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, type: str, severity: str, payload_json: str) -> Alert:
        row = Alert(type=type, severity=severity, payload_json=payload_json)
        self.session.add(row)
        self.session.flush()
        return row
