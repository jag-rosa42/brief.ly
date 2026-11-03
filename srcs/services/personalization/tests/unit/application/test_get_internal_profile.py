from uuid import UUID, uuid4

import pytest

from src.application.use_cases.get_internal_profile import GetInternalProfile
from src.domain.entities.profile import Profile
from src.domain.entities.saved_article import SavedArticle
from src.domain.exception import ProfileNotFoundError
from tests.fakes import FakeProfileRepository, FakeSavedArticleRepository


def _saved_article(account_id: UUID) -> SavedArticle:
    return SavedArticle(
        account_id=account_id,
        article_id=uuid4(),
        title="Test Article",
        source="Test Source",
        topic_id="Test Topic",
        summary="Summary",
        url="http://example.com/article",
        read_time_minutes=42,
        saved_at=None,
    )


def test_execute_returns_the_profile_and_its_saved_article_ids() -> None:
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["science", "sports"]
    )
    profile_repository = FakeProfileRepository()
    profile_repository.add(profile)
    saved_article_repository = FakeSavedArticleRepository()
    first = _saved_article(account_id=profile.account_id)
    second = _saved_article(account_id=profile.account_id)
    saved_article_repository.add(first)
    saved_article_repository.add(second)
    saved_article_repository.add(_saved_article(account_id=uuid4()))  # another account

    use_case = GetInternalProfile(profile_repository, saved_article_repository)
    result = use_case.execute(profile.account_id)

    assert result.profile == profile
    assert set(result.saved_article_ids) == {first.article_id, second.article_id}


def test_execute_returns_no_saved_article_ids_when_nothing_is_saved() -> None:
    profile = Profile.create(
        account_id=uuid4(), name="John", topic_ids=["science", "sports"]
    )
    profile_repository = FakeProfileRepository()
    profile_repository.add(profile)
    saved_article_repository = FakeSavedArticleRepository()

    use_case = GetInternalProfile(profile_repository, saved_article_repository)
    result = use_case.execute(profile.account_id)

    assert result.profile == profile
    assert result.saved_article_ids == []


def test_execute_raises_when_profile_does_not_exist() -> None:
    profile_repository = FakeProfileRepository()
    saved_article_repository = FakeSavedArticleRepository()
    use_case = GetInternalProfile(
        profile_repository=profile_repository,
        saved_article_repository=saved_article_repository,
    )

    with pytest.raises(ProfileNotFoundError):
        use_case.execute(uuid4())
