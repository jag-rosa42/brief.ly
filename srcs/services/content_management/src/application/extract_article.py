from src.application.ports import ArticleExtractor
from src.domain.entities.discovered_article import DiscoveredArticle
from src.domain.entities.extracted_article import ExtractedArticle


class ExtractArticle:
    def __init__(self, extractor: ArticleExtractor):
        self.extractor = extractor

    def execute(self, discovered: DiscoveredArticle
                ) -> ExtractedArticle:
        return self.extractor.extract(discovered)
