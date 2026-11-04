from unittest.mock import Mock
from uuid import uuid4

import pytest

from src.application.use_cases.articles import GetArticle
from src.domain.exception import ArticleNotFoundError
from src.domain.repositories import NormalizedArticleRepository


@pytest.fixture
def repository() -> Mock:
    return Mock(spec=NormalizedArticleRepository)


def test_returns_the_requested_article(repository: Mock, normalized_article) -> None:
    repository.get_by_id.return_value = normalized_article

    result = GetArticle(repository).execute(normalized_article.id)

    assert result == normalized_article
    repository.get_by_id.assert_called_once_with(normalized_article.id)


def test_raises_when_the_article_does_not_exist(repository: Mock) -> None:
    article_id = uuid4()
    repository.get_by_id.return_value = None

    with pytest.raises(ArticleNotFoundError):
        GetArticle(repository).execute(article_id)

    repository.get_by_id.assert_called_once_with(article_id)
