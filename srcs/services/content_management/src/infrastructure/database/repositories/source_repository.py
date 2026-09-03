from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.entities.source import Source
from src.infrastructure.database.models.source import SourceModel


class SqlAlchemySourceRepository:
    def __init__(self, session: Session):
        self._session: Session = session

    def update_last_successful_sync(
        self, source_id: UUID, synchronized_at: datetime
    ) -> None:
        statement: Select[tuple[SourceModel]] = select(SourceModel).where(
            SourceModel.id == source_id
        )
        source = self._session.scalars(statement).one()
        source.last_successful_sync_at = synchronized_at
        self.commit()

    def list_due(self, synchronized_at: datetime) -> list[Source]:
        statement: Select[tuple[SourceModel]] = select(SourceModel).where(
            SourceModel.enabled
        )

        sources = []
        for source in self._session.scalars(statement):
            if source.last_successful_sync_at is None:
                sources.append(self._to_source(source))
            else:
                delta = source.last_successful_sync_at + timedelta(
                    seconds=source.interval_seconds
                )
                if synchronized_at >= delta:
                    sources.append(self._to_source(source))
        return sources

    @staticmethod
    def _to_source(source: SourceModel) -> Source:
        return Source(
            id=source.id,
            category=source.category,
            language=source.language,
            interval_seconds=source.interval_seconds,
            enabled=source.enabled,
        )

    @staticmethod
    def _to_model(source: Source) -> SourceModel:
        return SourceModel(
            id=source.id,
            category=source.category,
            language=source.language,
            interval_seconds=source.interval_seconds,
            enabled=source.enabled,
        )

    def save(self, source: Source) -> None:
        source_model: SourceModel = self._to_model(source)
        self._session.add(source_model)

    def commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    def rollback(self) -> None:
        self._session.rollback()
