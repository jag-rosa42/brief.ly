from src.application.ports import ArticleExtractor
from src.domain.entities import DiscoveredArticle, NormalizedArticle


class ExtractArticle:
    def __init__(self, article_extractor: ArticleExtractor):
        self.article_extractor = article_extractor

    def execute(self, discovered: DiscoveredArticle) -> NormalizedArticle:
        return self.article_extractor.extract(discovered)
