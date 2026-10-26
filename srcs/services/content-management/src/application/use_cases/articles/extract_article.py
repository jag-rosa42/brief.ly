from src.application.port import ArticleExtractor
from src.domain.entities import DiscoveredArticle, NormalizedArticle


class ExtractArticle:
    def __init__(self, extractor: ArticleExtractor) -> None:
        self._extractor = extractor

    def execute(self, discovered: DiscoveredArticle) -> NormalizedArticle:
        return self._extractor.extract(discovered)
