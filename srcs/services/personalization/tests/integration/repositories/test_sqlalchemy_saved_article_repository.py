from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import delete
from sqlalchemy.orm import Session

from src.domain.entities.profile import Profile
from src.domain.entities.saved_article import SavedArticle
from src.infrastructure.database.models.profile import Profile as ProfileModel
from src.infrastructure.database.models.saved_article import (
    SavedArticle as SavedArticleModel,
)
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_saved_article_repository import (
    SqlAlchemySavedArticleRepository,
)


def test_list_for_account_returns_saved_articles_in_descending_order(
    db_session: Session,
) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)
    account_id = uuid4()
    profile = Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    SqlAlchemyProfileRepository(db_session).upsert(profile)

    saved_article1 = SavedArticle(
        account_id=account_id,
        article_id=uuid4(),
        title="Article 1",
        source="Source 1",
        topic_id="Topic 1",
        summary="Summary 1",
        url="http://example.com/article1",
        read_time_minutes=5,
        saved_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    saved_article2 = SavedArticle(
        account_id=account_id,
        article_id=uuid4(),
        title="Article 2",
        source="Source 2",
        topic_id="Topic 2",
        summary="Summary 2",
        url="http://example.com/article2",
        read_time_minutes=10,
        saved_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    db_session.add_all(
        [
            SavedArticleModel(**saved_article1.__dict__),
            SavedArticleModel(**saved_article2.__dict__),
        ]
    )
    db_session.commit()

    saved_articles = repository.list_for_account(account_id)

    assert saved_articles == [saved_article2, saved_article1]


def test_list_for_account_returns_empty_list_for_unknown_account(
    db_session: Session,
) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)

    saved_articles = repository.list_for_account(uuid4())

    assert saved_articles == []


def test_delete_removes_saved_article(db_session: Session) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)
    account_id = uuid4()
    profile = Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    SqlAlchemyProfileRepository(db_session).upsert(profile)
    article_id = uuid4()
    saved_article = SavedArticle(
        account_id=account_id,
        article_id=article_id,
        title="Article",
        source="Source",
        topic_id="Topic",
        summary="Summary",
        url="http://example.com/article",
        read_time_minutes=5,
        saved_at=None,
    )
    db_session.add(SavedArticleModel(**saved_article.__dict__))
    db_session.commit()

    repository.delete(account_id, article_id)

    assert repository.list_for_account(account_id) == []


def test_delete_nonexistent_saved_article_does_nothing(db_session: Session) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)
    account_id = uuid4()
    article_id = uuid4()

    # Ensure the saved article does not exist
    assert repository.list_for_account(account_id) == []

    # Attempt to delete the nonexistent saved article
    repository.delete(account_id, article_id)

    # Ensure the saved article still does not exist
    assert repository.list_for_account(account_id) == []


def test_delete_keeps_other_accounts_saved_article(db_session: Session) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)
    profile_repository = SqlAlchemyProfileRepository(db_session)
    account_id = uuid4()
    other_account_id = uuid4()
    profile_repository.upsert(
        Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    )
    profile_repository.upsert(
        Profile.create(account_id=other_account_id, name="Jane", topic_ids=["science"])
    )
    article_id = uuid4()
    saved_article = SavedArticle(
        account_id=account_id,
        article_id=article_id,
        title="Article",
        source="Source",
        topic_id="Topic",
        summary="Summary",
        url="http://example.com/article",
        read_time_minutes=5,
        saved_at=None,
    )
    other_saved_article = replace(saved_article, account_id=other_account_id)
    db_session.add_all(
        [
            SavedArticleModel(**saved_article.__dict__),
            SavedArticleModel(**other_saved_article.__dict__),
        ]
    )
    db_session.flush()

    repository.delete(account_id, article_id)

    assert repository.list_for_account(account_id) == []
    assert repository.list_for_account(other_account_id) == [other_saved_article]


def test_deleting_the_profile_deletes_its_saved_articles(db_session: Session) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)
    account_id = uuid4()
    profile = Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    SqlAlchemyProfileRepository(db_session).upsert(profile)
    saved_article = SavedArticle(
        account_id=account_id,
        article_id=uuid4(),
        title="Article",
        source="Source",
        topic_id="Topic",
        summary="Summary",
        url="http://example.com/article",
        read_time_minutes=5,
        saved_at=None,
    )
    db_session.add(SavedArticleModel(**saved_article.__dict__))
    db_session.flush()

    db_session.execute(delete(ProfileModel).where(ProfileModel.account_id == account_id))

    assert repository.list_for_account(account_id) == []


def _snapshot(account_id: UUID) -> SavedArticle:
    return SavedArticle(
        account_id=account_id,
        article_id=uuid4(),
        title="Article",
        source="Source",
        topic_id="Topic",
        summary=None,
        url="http://example.com/article",
        read_time_minutes=0,
    )


def test_add_inserts_the_saved_article_and_returns_its_saved_at(
    db_session: Session,
) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)
    account_id = uuid4()
    SqlAlchemyProfileRepository(db_session).upsert(
        Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    )
    saved_article = _snapshot(account_id)

    added = repository.add(saved_article)

    assert added == saved_article
    assert added.saved_at is not None
    assert repository.list_for_account(account_id) == [saved_article]


def test_exists_tells_if_the_account_saved_the_article(db_session: Session) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)
    account_id = uuid4()
    SqlAlchemyProfileRepository(db_session).upsert(
        Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    )
    saved_article = repository.add(_snapshot(account_id))

    assert repository.exists(account_id, saved_article.article_id) is True
    assert repository.exists(account_id, uuid4()) is False
    assert repository.exists(uuid4(), saved_article.article_id) is False


def test_count_for_account_counts_only_this_account(db_session: Session) -> None:
    repository = SqlAlchemySavedArticleRepository(db_session)
    profile_repository = SqlAlchemyProfileRepository(db_session)
    account_id = uuid4()
    other_account_id = uuid4()
    profile_repository.upsert(
        Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    )
    profile_repository.upsert(
        Profile.create(account_id=other_account_id, name="Jane", topic_ids=["science"])
    )
    repository.add(_snapshot(account_id))
    repository.add(_snapshot(account_id))
    repository.add(_snapshot(other_account_id))

    assert repository.count_for_account(account_id) == 2
    assert repository.count_for_account(uuid4()) == 0
