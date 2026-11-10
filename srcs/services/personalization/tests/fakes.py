from dataclasses import replace
from datetime import UTC, datetime
from types import TracebackType
from uuid import UUID

from src.application.exceptions import (
    ArticleCatalogUnavailableError,
    TopicCatalogUnavailableError,
)
from src.domain.entities.article import Article
from src.domain.entities.profile import Profile
from src.domain.entities.saved_article import SavedArticle
from src.domain.entities.topic import Topic


class FakeServiceTokenProvider:
    """Stands for shared_auth's ClientCredentialsTokenProvider: no Identity call.

    Gives `token`, or raises `error` when one is given (Identity down or
    refusing our credentials).
    """

    def __init__(
        self, token: str = "service-token", error: Exception | None = None
    ) -> None:
        self._token = token
        self._error = error

    def get_token(self) -> str:
        if self._error is not None:
            raise self._error
        return self._token


class FakeTopicCatalog:
    def __init__(self, topic_ids: list[str], available: bool = True) -> None:
        self._topic_ids = topic_ids
        self._available = available
        self.calls = 0

    def get_all(self) -> dict[str, Topic]:
        self.calls += 1
        if not self._available:
            raise TopicCatalogUnavailableError()
        return {topic_id: Topic(id=topic_id) for topic_id in self._topic_ids}


class FakeArticleCatalog:
    def __init__(self, articles: list[Article], available: bool = True) -> None:
        self._articles = {article.article_id: article for article in articles}
        self._available = available
        self.calls = 0

    def find_by_id(self, article_id: UUID) -> Article | None:
        self.calls += 1
        if not self._available:
            raise ArticleCatalogUnavailableError()
        return self._articles.get(article_id)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.committed = False

    def __enter__(self) -> FakeUnitOfWork:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass

    def flush(self) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


class FakeSavedArticleRepository:
    def __init__(self) -> None:
        self.saved_articles: dict[tuple[UUID, UUID], SavedArticle] = {}

    def add(self, saved_article: SavedArticle) -> SavedArticle:
        if saved_article.saved_at is None:
            saved_article = replace(saved_article, saved_at=datetime.now(UTC))
        self.saved_articles[(saved_article.account_id, saved_article.article_id)] = (
            saved_article
        )
        return saved_article

    def exists(self, account_id: UUID, article_id: UUID) -> bool:
        return (account_id, article_id) in self.saved_articles

    def count_for_account(self, account_id: UUID) -> int:
        return len(self.list_for_account(account_id))

    def list_for_account(self, account_id: UUID) -> list[SavedArticle]:
        return [
            saved_article
            for saved_article in self.saved_articles.values()
            if saved_article.account_id == account_id
        ]

    def delete(self, account_id: UUID, article_id: UUID) -> None:
        key = (account_id, article_id)
        if key in self.saved_articles:
            del self.saved_articles[key]


class FakeProfileRepository:
    def __init__(self) -> None:
        self._profiles_by_id: dict[UUID, Profile] = {}

    def add(self, profile: Profile) -> None:
        self._profiles_by_id[profile.account_id] = profile

    def upsert(self, profile: Profile) -> bool:
        created = profile.account_id not in self._profiles_by_id
        self._profiles_by_id[profile.account_id] = profile
        return created

    def find_by_id(self, account_id: UUID) -> Profile | None:
        return self._profiles_by_id.get(account_id)

    def find_by_id_for_update(self, account_id: UUID) -> Profile | None:
        return self.find_by_id(account_id)
