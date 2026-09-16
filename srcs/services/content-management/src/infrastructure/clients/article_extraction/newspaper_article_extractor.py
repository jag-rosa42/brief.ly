from collections.abc import Callable
from uuid import UUID, uuid4

from newspaper import Article as NewspaperArticle

from src.domain.entities import DiscoveredArticle, NormalizedArticle


class NewspaperArticleExtractor:
    def __init__(self, uuid_factory: Callable[[], UUID] = uuid4) -> None:
        self._uuid_factory = uuid_factory

    def extract(self, discovered: DiscoveredArticle) -> NormalizedArticle:
        newspaper_article = NewspaperArticle(discovered.url)
        newspaper_article.download()
        newspaper_article.parse()

        return self._to_normalized_article(newspaper_article, discovered)

    def _to_normalized_article(
        self,
        newspaper_article: NewspaperArticle,
        discovered: DiscoveredArticle,
    ) -> NormalizedArticle:
        return NormalizedArticle(
            id=self._uuid_factory(),
            discovered_article_external_id=discovered.external_id,
            url=newspaper_article.url,
            publisher_name=discovered.publisher_name,
            title=newspaper_article.title,
            description=discovered.description,
            content=newspaper_article.text,
            authors=newspaper_article.authors,
            image_url=newspaper_article.top_image,
            category=discovered.category,
            language=discovered.language,
            published_at=discovered.published_at,
        )
