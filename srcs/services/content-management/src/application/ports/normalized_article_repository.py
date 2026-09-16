from typing import Protocol
from uuid import UUID

from src.domain.entities import NormalizedArticle


class NormalizedArticleRepository(Protocol):
    def exists(
            self,
            source_id: UUID,
            discovered_article_external_id: str,
            ) -> bool:
        ...

    def save(
            self,
            source_id: UUID,
            normalized_article: NormalizedArticle,
            ) -> None:
        ...
