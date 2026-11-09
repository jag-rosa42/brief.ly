from urllib.parse import quote
from uuid import UUID

import httpx2 as httpx
from shared_errors import InfrastructureError

from src.application.models.article import Article
from src.application.models.topic_article_summary import (
    TopicArticleSummary,
)
from src.domain.value_objects.article_assessment import ArticleAssessment


class ContentManagementClient:
    def __init__(self, http_client: httpx.Client):
        self.http_client = http_client

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str | int] | None = None,
        json: dict[str, object] | None = None,
    ) -> httpx.Response:
        try:
            response = self.http_client.request(
                method,
                path,
                params=params,
                json=json,
                timeout=10,
            )
        except httpx.TransportError as exc:
            raise InfrastructureError("Content Management is unavailable.") from exc
        if response.status_code in (502, 503, 504):
            raise InfrastructureError("Content Management is unavailable.")
        response.raise_for_status()
        return response

    def list_missing_articles(self, limit: int) -> list[Article]:
        params = {"summary": "missing", "limit": limit}
        response = self._request("GET", "internal/v1/articles", params=params)
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
        self._request(
            "PUT",
            f"/internal/v1/articles/{article_id}/summary",
            json={
                "text": assessment.summary,
                "rejected": assessment.rejected,
                "quality_comment": assessment.quality_comment,
                "llm_model": llm_model,
                "generation_duration_ms": assessment.generation_duration_ms,
            },
        )

    def list_topics(self) -> list[str]:
        response = self._request("GET", "/internal/v1/topics")
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
        response = self._request(
            "GET",
            "/internal/v1/articles",
            params=params,
        )
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

    def save_topic_summary(
        self,
        topic_id: str,
        summary: str,
        llm_model: str,
        generation_duration_ms: int,
    ) -> None:
        self._request(
            "PUT",
            f"/internal/v1/topics/{quote(topic_id, safe='')}/summary",
            json={
                "text": summary,
                "llm_model": llm_model,
                "generation_duration_ms": generation_duration_ms,
            },
        )
