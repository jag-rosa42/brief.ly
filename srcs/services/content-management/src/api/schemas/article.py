from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from src.domain.entities import NormalizedArticle

Summary = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
]
SummaryLlmModel = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
QualityComment = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=2000),
]


class UpdateArticleSummaryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: Summary | None = Field(
        description="Null when rejected is true; non-empty when rejected is false."
    )
    llm_model: SummaryLlmModel
    rejected: bool
    quality_comment: QualityComment
    generation_duration_ms: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def validate_text_for_rejection(self) -> Self:
        if self.rejected and self.text is not None:
            raise ValueError("A rejected article must have a null summary.")
        if not self.rejected and self.text is None:
            raise ValueError("An accepted article must have a summary.")
        return self


class ArticleResponse(BaseModel):
    article_id: UUID
    title: str
    publisher_name: str
    url: str
    topic_id: str
    language: str
    content: str
    read_time_minutes: int
    summary: str | None
    summarized_at: datetime | None
    rejected: bool | None
    quality_comment: str | None
    generation_duration_ms: int | None

    @classmethod
    def from_domain(cls, article: NormalizedArticle) -> Self:
        return cls(
            article_id=article.id,
            title=article.title,
            publisher_name=article.publisher_name,
            url=article.url,
            topic_id=article.category,
            language=article.language,
            content=article.content,
            read_time_minutes=article.read_time_minutes,
            summary=(
                article.summary.text
                if article.summary is not None and not article.summary.rejected
                else None
            ),
            summarized_at=(
                article.summary.summarized_at if article.summary is not None else None
            ),
            rejected=article.summary.rejected if article.summary is not None else None,
            quality_comment=(
                article.summary.quality_comment if article.summary is not None else None
            ),
            generation_duration_ms=(
                article.summary.generation_duration_ms
                if article.summary is not None
                else None
            ),
        )


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
