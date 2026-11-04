from typing import Protocol
from uuid import UUID

from src.domain.entities import NormalizedArticle


class NormalizedArticleRepository(Protocol):
    def list_by_topic_id(
        self,
        topic_id: str,
        limit: int,
    ) -> list[NormalizedArticle]: ...

    def list_missing_summary(self, limit: int) -> list[NormalizedArticle]: ...

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
