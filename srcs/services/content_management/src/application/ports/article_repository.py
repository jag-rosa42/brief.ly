from typing import Protocol
from uuid import UUID

from src.domain.entities.extracted_article import ExtractedArticle


class ArticleRepository(Protocol):
    def exists(
            self,
            source_id: UUID,
            external_id: str,
            ) -> bool:
        ...

    def save(
            self,
            source_id: UUID,
            article: ExtractedArticle,
            ) -> None:
        ...
