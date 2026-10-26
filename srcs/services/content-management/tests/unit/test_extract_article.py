from unittest.mock import Mock

from src.application.use_cases.articles import ExtractArticle


def test_extract_article_delegates_the_discovered_article(discovered_article):
    normalized_article = object()
    article_extractor = Mock()
    article_extractor.extract.return_value = normalized_article

    result = ExtractArticle(article_extractor).execute(discovered_article)

    assert result is normalized_article
    article_extractor.extract.assert_called_once_with(discovered_article)
