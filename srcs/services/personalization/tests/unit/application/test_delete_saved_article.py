from uuid import UUID, uuid4

from src.application.use_cases.delete_saved_article import DeleteSavedArticle
from src.domain.entities.saved_article import SavedArticle
from tests.fakes import FakeSavedArticleRepository, FakeUnitOfWork


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


def test_execute_deletes_the_saved_article_and_commits() -> None:
    account_id = uuid4()
    saved_article = _saved_article(account_id=account_id)
    saved_article_repository = FakeSavedArticleRepository()
    saved_article_repository.add(saved_article)

    uow = FakeUnitOfWork()
    use_case = DeleteSavedArticle(uow, saved_article_repository=saved_article_repository)
    use_case.execute(account_id, saved_article.article_id)

    assert len(saved_article_repository.saved_articles) == 0
    assert saved_article not in saved_article_repository.saved_articles
    assert uow.committed is True


def test_execute_does_nothing_when_the_article_is_not_saved() -> None:
    account_id = uuid4()
    saved_article = _saved_article(account_id=account_id)
    saved_article_repository = FakeSavedArticleRepository()
    saved_article_repository.add(saved_article)

    use_case = DeleteSavedArticle(
        FakeUnitOfWork(), saved_article_repository=saved_article_repository
    )
    use_case.execute(account_id, uuid4())

    assert len(saved_article_repository.saved_articles) == 1
    assert saved_article_repository.list_for_account(account_id) == [saved_article]
