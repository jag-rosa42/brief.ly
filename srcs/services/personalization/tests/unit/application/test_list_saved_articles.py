from uuid import UUID, uuid4

from src.application.use_cases.list_saved_articles import ListSavedArticles
from src.domain.entities.saved_article import SavedArticle
from tests.fakes import FakeSavedArticleRepository


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


def test_execute_returns_the_accounts_saved_articles() -> None:
    account_id = uuid4()
    saved_article1 = _saved_article(account_id=account_id)
    saved_article2 = _saved_article(account_id=account_id)
    saved_article_repository = FakeSavedArticleRepository()
    saved_article_repository.add(saved_article1)
    saved_article_repository.add(saved_article2)
    saved_article_repository.add(_saved_article(account_id=uuid4()))

    use_case = ListSavedArticles(saved_article_repository=saved_article_repository)
    result = use_case.execute(account_id)

    assert len(result) == 2
    assert saved_article1 in result
    assert saved_article2 in result


def test_execute_returns_empty_list_when_no_saved_articles() -> None:
    account_id = uuid4()
    saved_article_repository = FakeSavedArticleRepository()

    use_case = ListSavedArticles(saved_article_repository=saved_article_repository)
    result = use_case.execute(account_id)

    assert result == []
