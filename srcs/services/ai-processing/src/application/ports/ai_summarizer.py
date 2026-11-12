from typing import Protocol

from src.application.models.answer_validation_error import AnswerValidationError
from src.application.models.article import Article
from src.domain.value_objects.article_assessment import ArticleAssessment


class ArticleSummarizerPort(Protocol):
    def ai_summarize_article(
        self, article: Article, *, previous_failure: AnswerValidationError | None = None
    ) -> ArticleAssessment: ...


class TopicSummarizerPort(Protocol):
    def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str: ...
