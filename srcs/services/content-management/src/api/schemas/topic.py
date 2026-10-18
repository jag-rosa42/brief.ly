from typing import Self

from pydantic import BaseModel

from src.domain.entities import Topic


class TopicResponse(BaseModel):
    id: str

    @classmethod
    def from_domain(cls, topic: Topic) -> Self:
        return cls(
            id=topic.id,
        )
