from urllib.parse import quote
from uuid import UUID

from httpx2 import Client

from src.application.models.article import Article
from src.application.models.article_assessment import ArticleAssessment
from src.application.models.topic_article_summary import (
    TopicArticleSummary,
)


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

    def list_topics(self) -> list[str]:
        response = self.http_client.get(
            "/internal/v1/topics",
            timeout=10,
        )
        response.raise_for_status()
        topics = response.json()
        if not isinstance(topics, list):
            raise ValueError("Content Management returned invalid topics")
        topic_ids = [topic["id"] for topic in topics]
        if any(not isinstance(topic_id, str) or not topic_id for topic_id in topic_ids):
            raise ValueError("Content Management returned an invalid topic ID")
        return topic_ids

    def list_topic_article_summaries(
        self, topic_id: str, limit: int
    ) -> list[TopicArticleSummary]:
        params: dict[str, str | int] = {"topic_id": topic_id, "limit": limit}
        response = self.http_client.get(
            "/internal/v1/articles",
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        items = data["items"]
        if not isinstance(items, list) or len(items) > limit:
            raise ValueError("Content Management returned an invalid topic article list")
        summaries = [
            TopicArticleSummary(
                article_id=UUID(item["article_id"]), summary=item["summary"]
            )
            for item in items
        ]
        if any(not isinstance(item.summary, str) for item in summaries):
            raise ValueError("Content Management returned an invalid article summary")
        return summaries

    def save_topic_summary(self, topic_id: str, summary: str, llm_model: str) -> None:
        response = self.http_client.put(
            f"/internal/v1/topics/{quote(topic_id, safe='')}/summary",
            json={"text": summary, "llm_model": llm_model},
            timeout=10,
        )
        response.raise_for_status()
