from src.application.port.article_catalog import ArticleCatalog
from src.application.port.profile_reader import ProfileReader
from src.application.port.topic_catalog import TopicCatalog
from src.domain.entities.briefing import Briefing, TopicCluster
from src.domain.entities.profile import Profile
from src.domain.entities.topic import Topic
from src.domain.exception import ProfileNotFoundError


class GetBriefing:
    def __init__(
        self,
        profile_reader: ProfileReader,
        topic_catalog: TopicCatalog,
        article_catalog: ArticleCatalog,
    ) -> None:
        self._profiles: ProfileReader = profile_reader
        self._topic_catalog: TopicCatalog = topic_catalog
        self._article_catalog: ArticleCatalog = article_catalog

    def execute(self, user_token: str) -> Briefing:
        # The profile first: without it there is nothing to build, so Content
        # Management is not called.
        profile: Profile | None = self._profiles.get(user_token)
        if profile is None:
            raise ProfileNotFoundError()

        topics: dict[str, Topic] = self._topic_catalog.get_all()
        clusters = tuple(
            self._build_cluster(topic_id, topics.get(topic_id))
            for topic_id in profile.topic_ids
        )
        return Briefing(profile=profile, topic_clusters=clusters)

    def _build_cluster(self, topic_id: str, topic: Topic | None) -> TopicCluster:
        return TopicCluster(
            topic_id=topic_id,
            summary=topic.summary if topic is not None else None,
            articles=tuple(self._article_catalog.list_by_topic(topic_id)),
        )
