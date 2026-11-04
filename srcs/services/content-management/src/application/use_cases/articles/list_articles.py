from src.domain.entities import NormalizedArticle
from src.domain.exception import TopicNotFoundError
from src.domain.repositories import NormalizedArticleRepository, TopicRepository


class ListArticles:
    def __init__(
        self,
        article_repository: NormalizedArticleRepository,
        topic_repository: TopicRepository,
    ) -> None:
        self._article_repository = article_repository
        self._topic_repository = topic_repository

    def execute(
        self,
        *,
        topic_id: str | None,
        summary_missing: bool,
        limit: int,
    ) -> list[NormalizedArticle]:
        if topic_id is None:
            if not summary_missing:
                raise ValueError("An article filter is required.")
            return self._article_repository.list_missing_summary(limit)

        if summary_missing:
            raise ValueError("Article filters are mutually exclusive.")
        if not self._topic_repository.exists(topic_id):
            raise TopicNotFoundError(topic_id)
        return self._article_repository.list_by_topic_id(topic_id, limit)
