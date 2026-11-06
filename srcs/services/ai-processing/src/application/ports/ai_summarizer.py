from typing import Protocol

from src.application.models.article import Article
from src.application.models.article_assessment import ArticleAssessment


class AiSummarizerPort(Protocol):
    def ai_summarize_article(self, article: Article) -> ArticleAssessment: ...

