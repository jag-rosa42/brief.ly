from typing import Protocol

from src.domain.entities import DiscoveredArticle, NormalizedArticle


class ArticleExtractor(Protocol):
    def extract(self, discovered: DiscoveredArticle) -> NormalizedArticle: ...
