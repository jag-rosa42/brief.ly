from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities import NormalizedArticle


class ArticleResponse(BaseModel):
    article_id: UUID
    title: str
    source: str
    url: str
    topic_id: str
    read_time_minutes: int
    summary: str | None
    summarized_at: datetime | None

    @classmethod
    def from_domain(cls, article: NormalizedArticle) -> Self:
        return cls(
            article_id=article.id,
            title=article.title,
            source=article.publisher_name,
            url=article.url,
            topic_id=article.category,
            read_time_minutes=article.read_time_minutes,
            summary=article.summary,
            summarized_at=article.summarized_at,
        )


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
