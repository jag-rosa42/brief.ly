from typing import Protocol

from src.domain.entities import DiscoveredArticle, Source


class ArticleDiscoverer(Protocol):
    def discover(self, source: Source) -> list[DiscoveredArticle]: ...
