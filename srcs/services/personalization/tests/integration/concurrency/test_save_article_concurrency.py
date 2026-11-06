"""
Concurrency test for POST /me/saved-articles/{article_id}.

The request and the concurrent save run in independent database transactions
(``concurrent_clients``), so the data is really committed: the test deletes it
at the end.
"""

import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, delete
from sqlalchemy.orm import Session

from src.api.dependencies.article_catalog import get_article_catalog
from src.domain.entities.article import Article
from src.domain.entities.profile import Profile
from src.domain.entities.saved_article import MAX_SAVED_ARTICLES, SavedArticle
from src.infrastructure.database.models.profile import Profile as ProfileModel
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_saved_article_repository import (
    SqlAlchemySavedArticleRepository,
)
from src.main import app
from tests.fakes import FakeArticleCatalog
from tests.fixtures.auth import AuthHeaders
from tests.routes import me_saved_article


def _article() -> Article:
    return Article(
        article_id=uuid4(),
        title="Article",
        source="Source",
        topic_id="science",
        summary=None,
        url="https://example.com/article",
        read_time_minutes=0,
    )


@pytest.fixture
def account_id(engine: Engine) -> Generator[UUID]:
    account_id: UUID = uuid4()
    try:
        yield account_id
    finally:
        # ON DELETE CASCADE removes the profile's saved articles too.
        with Session(engine) as session:
            session.execute(
                delete(ProfileModel).where(ProfileModel.account_id == account_id)
            )
            session.commit()


@pytest.fixture
def article() -> Generator[Article]:
    article = _article()
    app.dependency_overrides[get_article_catalog] = lambda: FakeArticleCatalog([article])
    try:
        yield article
    finally:
        app.dependency_overrides.pop(get_article_catalog, None)


def test_a_save_waits_for_a_concurrent_save_before_checking_the_limit(
    concurrent_clients: tuple[TestClient, TestClient],
    engine: Engine,
    account_id: UUID,
    article: Article,
    auth_headers: AuthHeaders,
) -> None:
    # One place left before the limit.
    with Session(engine) as session:
        SqlAlchemyProfileRepository(session).upsert(
            Profile.create(account_id=account_id, name="John", topic_ids=["science"])
        )
        saved_articles = SqlAlchemySavedArticleRepository(session)
        for _ in range(MAX_SAVED_ARTICLES - 1):
            saved_articles.add(SavedArticle.create(account_id, _article()))
        session.commit()

    client, _ = concurrent_clients
    with Session(engine) as concurrent_save, ThreadPoolExecutor(max_workers=1) as pool:
        # Another save is in progress: it holds the profile lock and has added
        # the 12th article, but has not committed yet.
        SqlAlchemyProfileRepository(concurrent_save).find_by_id_for_update(account_id)
        SqlAlchemySavedArticleRepository(concurrent_save).add(
            SavedArticle.create(account_id, _article())
        )

        response = pool.submit(
            client.post,
            me_saved_article(article.article_id),
            headers=auth_headers(account_id),
        )
        # Give the request time to reach the lock. Without the lock, it would
        # count 11 articles now and save a 13th.
        time.sleep(0.3)
        concurrent_save.commit()

        assert response.result(timeout=5).status_code == 409

    with Session(engine) as session:
        count = SqlAlchemySavedArticleRepository(session).count_for_account(account_id)
    assert count == MAX_SAVED_ARTICLES
