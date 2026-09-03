from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Source:
    id: UUID
    category: str
    language: str
    interval_seconds: int
    enabled: bool
