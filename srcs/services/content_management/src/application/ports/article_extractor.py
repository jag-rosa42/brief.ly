from typing import Protocol

from src.domain.entities.discovered_article import DiscoveredArticle
from src.domain.entities.extracted_article import ExtractedArticle


class ArticleExtractor(Protocol):
    def extract(self,
                discovered: DiscoveredArticle
                ) -> ExtractedArticle:
        ...
