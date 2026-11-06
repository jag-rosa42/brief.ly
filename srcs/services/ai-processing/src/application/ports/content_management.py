from typing import Protocol
from uuid import UUID

from src.application.models.article import Article
from src.application.models.article_assessment import ArticleAssessment
from src.application.models.topic_article_summary import TopicArticleSummaryPage


class ContentManagementPort(Protocol):
    def list_missing_articles(self, limit: int) -> list[Article]: ...

    def save_article_assessment(
        self, article_id: UUID, assessment: ArticleAssessment, llm_model: str
    ) -> None: ...

