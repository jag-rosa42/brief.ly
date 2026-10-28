from typing import Protocol
from uuid import UUID

from src.domain.entities import NormalizedArticle


class NormalizedArticleRepository(Protocol):
    def find_existing_external_ids(
        self,
        source_id: UUID,
        external_ids: list[str],
    ) -> set[str]: ...

    def save(
        self,
        source_id: UUID,
        normalized_article: NormalizedArticle,
    ) -> None: ...
