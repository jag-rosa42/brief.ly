from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.application.use_cases.articles import ListArticles
from src.domain.entities import NormalizedArticle
from src.domain.exception import TopicNotFoundError
from src.domain.repositories import NormalizedArticleRepository, TopicRepository


@pytest.fixture
def normalized_article() -> NormalizedArticle:
    return NormalizedArticle(
        id=uuid4(),
        discovered_article_external_id="science-en",
        url="https://example.com/article",
        publisher_name="Example source",
        title="Example article",
        description=None,
        content="Example article content",
        authors=None,
        image_url=None,
        published_at=None,
        category="science",
        language="en",
    )


@pytest.fixture
def article_repository() -> Mock:
    return Mock(spec=NormalizedArticleRepository)


@pytest.fixture
def topic_repository() -> Mock:
    return Mock(spec=TopicRepository)


def test_lists_articles_for_an_existing_topic(
    normalized_article: NormalizedArticle,
    article_repository: Mock,
    topic_repository: Mock,
) -> None:
    topic_repository.exists.return_value = True
    article_repository.list_by_topic_id.return_value = [normalized_article]
    use_case = ListArticles(article_repository, topic_repository)

    result = use_case.execute(topic_id="science", summary_missing=False, limit=12)

    assert result == [normalized_article]
    topic_repository.exists.assert_called_once_with("science")
    article_repository.list_by_topic_id.assert_called_once_with("science", 12)


def test_rejects_an_unknown_topic(
    article_repository: Mock,
    topic_repository: Mock,
) -> None:
    topic_repository.exists.return_value = False
    use_case = ListArticles(article_repository, topic_repository)

    with pytest.raises(TopicNotFoundError):
        use_case.execute(topic_id="unknown", summary_missing=False, limit=25)

    article_repository.list_by_topic_id.assert_not_called()


def test_lists_articles_without_a_summary(
    normalized_article: NormalizedArticle,
    article_repository: Mock,
    topic_repository: Mock,
) -> None:
    article_repository.list_missing_summary.return_value = [normalized_article]
    use_case = ListArticles(article_repository, topic_repository)

    result = use_case.execute(topic_id=None, summary_missing=True, limit=5)

    assert result == [normalized_article]
    article_repository.list_missing_summary.assert_called_once_with(5)
    topic_repository.exists.assert_not_called()


@pytest.mark.parametrize(
    ("topic_id", "summary_missing"),
    [(None, False), ("science", True)],
)
def test_rejects_invalid_filter_combinations(
    topic_id: str | None,
    summary_missing: bool,
    article_repository: Mock,
    topic_repository: Mock,
) -> None:
    use_case = ListArticles(article_repository, topic_repository)

    with pytest.raises(ValueError):
        use_case.execute(
            topic_id=topic_id,
            summary_missing=summary_missing,
            limit=25,
        )
