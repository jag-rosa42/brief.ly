from typing import Self
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities.article import Article
from src.domain.entities.briefing import Briefing, TopicCluster
from src.domain.entities.profile import Profile

# Response of GET /briefing (docs/api/03_morning-briefing.md).


class BriefingProfileResponse(BaseModel):
    name: str
    topic_ids: list[str]
    saved_article_ids: list[UUID]

    @classmethod
    def from_domain(cls, profile: Profile) -> Self:
        return cls(
            name=profile.name,
            topic_ids=list(profile.topic_ids),
            saved_article_ids=list(profile.saved_article_ids),
        )


class BriefingArticleResponse(BaseModel):
    article_id: UUID
    title: str
    publisher_name: str
    url: str
    summary: str | None
    read_time_minutes: int
    topic_id: str

    @classmethod
    def from_domain(cls, article: Article) -> Self:
        return cls(
            article_id=article.article_id,
            title=article.title,
            publisher_name=article.publisher_name,
            url=article.url,
            summary=article.summary,
            read_time_minutes=article.read_time_minutes,
            topic_id=article.topic_id,
        )


class TopicClusterResponse(BaseModel):
    topic_id: str
    summary: str | None
    articles: list[BriefingArticleResponse]

    @classmethod
    def from_domain(cls, cluster: TopicCluster) -> Self:
        return cls(
            topic_id=cluster.topic_id,
            summary=cluster.summary,
            articles=[
                BriefingArticleResponse.from_domain(article)
                for article in cluster.articles
            ],
        )


class BriefingResponse(BaseModel):
    profile: BriefingProfileResponse
    topic_clusters: list[TopicClusterResponse]

    @classmethod
    def from_domain(cls, briefing: Briefing) -> Self:
        return cls(
            profile=BriefingProfileResponse.from_domain(briefing.profile),
            topic_clusters=[
                TopicClusterResponse.from_domain(cluster)
                for cluster in briefing.topic_clusters
            ],
        )
