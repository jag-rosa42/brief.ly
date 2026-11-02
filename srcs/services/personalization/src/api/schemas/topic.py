from typing import Self

from pydantic import (
    BaseModel,
)

from src.domain.entities.topic import (
    Topic,
)


class TopicResponse(BaseModel):
    id: str

    @classmethod
    def from_domain(cls, topic: Topic) -> Self:
        return cls(
            id=topic.id,
        )


class TopicsResponse(BaseModel):
    items: list[TopicResponse]

    @classmethod
    def from_domain(cls, topics: list[Topic]) -> Self:
        return cls(
            items=[TopicResponse.from_domain(topic) for topic in topics],
        )
