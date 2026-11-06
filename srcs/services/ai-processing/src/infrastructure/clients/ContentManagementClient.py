from uuid import UUID

from httpx2 import Client

from src.application.models.article import Article
from src.application.models.article_assessment import ArticleAssessment


class ContentManagementClient:
    def __init__(self, http_client: Client):
        self.http_client = http_client

    def list_missing_articles(self, limit: int) -> list[Article]:
        params = {"summary": "missing", "limit": limit}
        response = self.http_client.get(
            "internal/v1/articles", params=params, timeout=10
        )
        response.raise_for_status()
        data = response.json()
        articles_received = data["items"]
        articles: list[Article] = []
        for article_item in articles_received:
            article = Article(
                id=UUID(article_item["article_id"]),
                title=article_item["title"],
                content=article_item["content"],
                language=article_item["language"],
                topic_id=article_item["topic_id"],
            )
            articles.append(article)
        return articles

    def save_article_assessment(
        self,
        article_id: UUID,
        assessment: ArticleAssessment,
        llm_model: str,
    ) -> None:
        response = self.http_client.put(
            f"/internal/v1/articles/{article_id}/summary",
            json={
                "text": assessment.summary,
                "rejected": assessment.rejected,
                "quality_comment": assessment.quality_comment,
                "llm_model": llm_model,
                "generation_duration_ms": assessment.generation_duration_ms,
            },
            timeout=10,
        )
        response.raise_for_status()

