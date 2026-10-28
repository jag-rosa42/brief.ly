from typing import Protocol

from src.domain.entities import DiscoveredArticle, NormalizedArticle


class ArticleExtractionError(Exception):
    """An expected failure while downloading or parsing an article."""


class ArticleExtractor(Protocol):
    def extract(self, discovered: DiscoveredArticle) -> NormalizedArticle: ...
