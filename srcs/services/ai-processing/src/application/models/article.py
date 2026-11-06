from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class Article:
    id: UUID
    title: str
    content: str
    language: str
    topic_id: str
