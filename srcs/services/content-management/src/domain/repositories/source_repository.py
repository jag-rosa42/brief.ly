from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.domain.entities import Source


class SourceRepository(Protocol):
    def update_last_successful_sync(
        self,
        source_id: UUID,
        synchronized_at: datetime,
    ) -> None: ...

    def list_due(
        self,
        synchronized_at: datetime,
    ) -> list[Source]: ...

    def save(self, source: Source) -> None: ...
