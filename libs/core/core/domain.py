from dataclasses import dataclass


@dataclass(slots=True)
class Narrative:
    id: str
    content: str
