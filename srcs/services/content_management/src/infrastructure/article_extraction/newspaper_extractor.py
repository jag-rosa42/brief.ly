from collections.abc import Callable
from uuid import UUID, uuid4

from newspaper import Article

from src.domain.entities.discovered_article import DiscoveredArticle
from src.domain.entities.extracted_article import ExtractedArticle


class NewspaperExtractor:
    def __init__(self, uuid_factory: Callable[[], UUID] = uuid4) -> None:
        self._uuid_factory = uuid_factory

    def extract(self, discovered: DiscoveredArticle) -> ExtractedArticle:
        extracted = Article(discovered.url)
        extracted.download()
        extracted.parse()

        return self._to_extracted_article(extracted, discovered)

    def _to_extracted_article(
        self,
        extracted: Article,
        discovered: DiscoveredArticle,
    ) -> ExtractedArticle:
        return ExtractedArticle(
            id=self._uuid_factory(),
            external_id=discovered.external_id,
            url=extracted.url,
            editor=discovered.editor,
            title=extracted.title,
            description=discovered.description,
            content=extracted.text,
            authors=extracted.authors,
            image_url=extracted.top_image,
            category=discovered.category,
            language=discovered.language,
            published_at=discovered.published_at,
        )
