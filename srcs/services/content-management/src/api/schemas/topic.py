from datetime import datetime
from typing import Self

from pydantic import BaseModel

from src.domain.entities import Topic


class TopicResponse(BaseModel):
    id: str
    summary: str | None
    summarized_at: datetime | None

    @classmethod
    def from_domain(cls, topic: Topic) -> Self:
        return cls(
            id=topic.id,
            summary=topic.summary.text if topic.summary is not None else None,
            summarized_at=(
                topic.summary.summarized_at if topic.summary is not None else None
            ),
        )
