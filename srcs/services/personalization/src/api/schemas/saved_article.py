from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.saved_article import SavedArticle


class SavedArticleResponse(BaseModel):
    article_id: UUID
    title: str
    publisher_name: str
    topic_id: str
    summary: str | None
    url: str
    read_time_minutes: int
    saved_at: datetime

    @classmethod
    def from_domain(cls, saved_article: SavedArticle) -> Self:
        """Build the response from a saved article loaded from the database."""

        if saved_article.saved_at is None:
            raise ValueError("The saved article must be loaded from the database")
        return cls(
            article_id=saved_article.article_id,
            title=saved_article.title,
            publisher_name=saved_article.source,
            topic_id=saved_article.topic_id,
            summary=saved_article.summary,
            url=saved_article.url,
            read_time_minutes=saved_article.read_time_minutes,
            saved_at=saved_article.saved_at,
        )


class SavedArticlesResponse(BaseModel):
    items: list[SavedArticleResponse]

    @classmethod
    def from_domain(cls, saved_articles: list[SavedArticle]) -> Self:
        return cls(
            items=[
                SavedArticleResponse.from_domain(saved_article)
                for saved_article in saved_articles
            ]
        )
