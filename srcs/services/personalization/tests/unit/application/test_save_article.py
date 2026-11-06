from uuid import UUID, uuid4

import pytest

from src.application.exceptions import ArticleCatalogUnavailableError
from src.application.use_cases.save_article import SaveArticle
from src.domain.entities.article import Article
from src.domain.entities.profile import Profile
from src.domain.entities.saved_article import MAX_SAVED_ARTICLES, SavedArticle
from src.domain.exception import (
    ArticleAlreadySavedError,
    ArticleNotFoundError,
    ProfileNotFoundError,
    SavedArticlesLimitReachedError,
)
from tests.fakes import (
    FakeArticleCatalog,
    FakeProfileRepository,
    FakeSavedArticleRepository,
    FakeUnitOfWork,
)


def _article() -> Article:
    return Article(
        article_id=uuid4(),
        title="Article",
        source="TechDaily",
        topic_id="science",
        summary=None,
        url="https://example.com/article",
        read_time_minutes=0,
    )


class _Setup:
    """A profile for `account_id`, and a catalog that knows `article`."""

    def __init__(self, catalog_available: bool = True) -> None:
        self.account_id: UUID = uuid4()
        self.article: Article = _article()
        self.uow = FakeUnitOfWork()
        self.profiles = FakeProfileRepository()
        self.profiles.add(
            Profile.create(self.account_id, name="John", topic_ids=["science"])
        )
        self.saved_articles = FakeSavedArticleRepository()
        self.catalog = FakeArticleCatalog([self.article], available=catalog_available)
        self.use_case = SaveArticle(
            self.uow, self.profiles, self.saved_articles, self.catalog
        )

    def save_others(self, count: int) -> None:
        for _ in range(count):
            self.saved_articles.add(SavedArticle.create(self.account_id, _article()))


def test_execute_saves_a_snapshot_of_the_article_and_commits() -> None:
    setup = _Setup()

    saved = setup.use_case.execute(setup.account_id, setup.article.article_id)

    assert saved == SavedArticle.create(setup.account_id, setup.article)
    assert saved.saved_at is not None
    assert setup.saved_articles.list_for_account(setup.account_id) == [saved]
    assert setup.uow.committed is True


def test_execute_raises_when_the_article_is_unknown() -> None:
    setup = _Setup()

    with pytest.raises(ArticleNotFoundError):
        setup.use_case.execute(setup.account_id, uuid4())

    assert setup.uow.committed is False


def test_execute_raises_when_the_profile_does_not_exist() -> None:
    setup = _Setup()

    with pytest.raises(ProfileNotFoundError):
        setup.use_case.execute(uuid4(), setup.article.article_id)

    assert setup.uow.committed is False


def test_execute_raises_when_the_article_is_already_saved() -> None:
    setup = _Setup()
    setup.use_case.execute(setup.account_id, setup.article.article_id)

    with pytest.raises(ArticleAlreadySavedError):
        setup.use_case.execute(setup.account_id, setup.article.article_id)


def test_execute_saves_the_last_article_under_the_limit() -> None:
    setup = _Setup()
    setup.save_others(MAX_SAVED_ARTICLES - 1)

    setup.use_case.execute(setup.account_id, setup.article.article_id)

    assert setup.saved_articles.count_for_account(setup.account_id) == MAX_SAVED_ARTICLES


def test_execute_raises_when_the_limit_is_reached() -> None:
    setup = _Setup()
    setup.save_others(MAX_SAVED_ARTICLES)

    with pytest.raises(SavedArticlesLimitReachedError):
        setup.use_case.execute(setup.account_id, setup.article.article_id)

    assert setup.saved_articles.count_for_account(setup.account_id) == MAX_SAVED_ARTICLES
    assert setup.uow.committed is False


def test_execute_raises_when_the_catalog_is_unavailable() -> None:
    setup = _Setup(catalog_available=False)

    with pytest.raises(ArticleCatalogUnavailableError):
        setup.use_case.execute(setup.account_id, setup.article.article_id)

    assert setup.saved_articles.list_for_account(setup.account_id) == []
