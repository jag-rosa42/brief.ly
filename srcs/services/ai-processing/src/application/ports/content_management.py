from typing import Protocol
from uuid import UUID

from src.application.models.article import Article
from src.application.models.topic_article_summary import TopicArticleSummary
from src.domain.value_objects.article_assessment import ArticleAssessment


class ArticleContentManagementPort(Protocol):
    def list_missing_articles(self, limit: int) -> list[Article]: ...

    def save_article_assessment(
        self, article_id: UUID, assessment: ArticleAssessment, llm_model: str
    ) -> None: ...


class TopicContentManagementPort(Protocol):
    def list_topics(self) -> list[str]: ...

    def list_topic_article_summaries(
        self, topic_id: str, limit: int
    ) -> list[TopicArticleSummary]: ...

    def save_topic_summary(self, topic_id: str, summary: str, llm_model: str) -> None: ...
