from typing import Protocol

from src.domain.entities.discovered_article import DiscoveredArticle
from src.domain.entities.source import Source


class ArticleDiscoverer(Protocol):
    def discover(self, source: Source) -> list[DiscoveredArticle]:
        ...
