from dataclasses import dataclass

from src.domain.entities.article import Article
from src.domain.entities.profile import Profile


@dataclass(frozen=True)
class TopicCluster:
    """One of the user's interests, with its summary and its articles."""

    topic_id: str
    summary: str | None
    articles: tuple[Article, ...]


@dataclass(frozen=True)
class Briefing:
    profile: Profile
    topic_clusters: tuple[TopicCluster, ...]
