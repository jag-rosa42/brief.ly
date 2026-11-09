from typing import Protocol

from src.application.models.article import Article
from src.domain.value_objects.article_assessment import ArticleAssessment


class ArticleSummarizerPort(Protocol):
    def ai_summarize_article(self, article: Article) -> ArticleAssessment: ...


class TopicSummarizerPort(Protocol):
    def ai_summarize_topic(self, topic_id: str, summaries: list[str]) -> str: ...
