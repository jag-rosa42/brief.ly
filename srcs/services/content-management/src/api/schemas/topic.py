from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from src.domain.entities import Topic


class UpdateTopicSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    ]
    llm_model: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
    ]
    generation_duration_ms: Annotated[int, Field(ge=0)]


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
