from .domain import Narrative


class InMemoryNarrativeRepo:
    def __init__(self) -> None:
        self._items: dict[str, Narrative] = {}

    def save(self, narrative: Narrative) -> None:
        self._items[narrative.id] = narrative

    def get(self, narrative_id: str) -> Narrative | None:
        return self._items.get(narrative_id)
