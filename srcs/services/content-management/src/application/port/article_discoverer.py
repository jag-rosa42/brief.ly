from typing import Protocol

from src.domain.entities import DiscoveredArticle, Source


class ArticleDiscoveryError(Exception):
    """An expected failure while querying an external article provider."""


class ArticleDiscoverer(Protocol):
    def discover(self, source: Source) -> list[DiscoveredArticle]: ...
