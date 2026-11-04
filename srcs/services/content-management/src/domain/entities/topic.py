from dataclasses import dataclass

from src.domain.entities.topic_summary import TopicSummary


@dataclass(frozen=True)
class Topic:
    id: str
    summary: TopicSummary | None = None
