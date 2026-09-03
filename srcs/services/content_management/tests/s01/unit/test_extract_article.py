from unittest.mock import Mock

from src.application.extract_article import ExtractArticle


def test_extract_article_delegates_the_discovered_article(discovered):
    extracted = object()
    extractor = Mock()
    extractor.extract.return_value = extracted

    result = ExtractArticle(extractor).execute(discovered)

    assert result is extracted
    extractor.extract.assert_called_once_with(discovered)
