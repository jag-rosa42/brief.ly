from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.entities import Source
from src.infrastructure.database.models.source import SourceModel


class SqlAlchemySourceRepository:
    def __init__(self, session: Session):
        self._session: Session = session

    def update_last_successful_sync(
        self, source_id: UUID, synchronized_at: datetime
    ) -> None:
        """
        Update last_successful_sync of a source with synchronized_at value.
        This function doesnt commit the changes.
        """
        statement: Select[tuple[SourceModel]] = select(SourceModel).where(
            SourceModel.id == source_id
        )
        source_model = self._session.scalars(statement).one()
        source_model.last_successful_sync_at = synchronized_at

    def list_due(self, synchronized_at: datetime) -> list[Source]:
        statement: Select[tuple[SourceModel]] = select(SourceModel).where(
            SourceModel.enabled
        )
        source_list = []
        for source_model in self._session.scalars(statement):
            if self._is_not_synced(source_model, synchronized_at):
                source_list.append(self._to_domain(source_model))
        return source_list

    @staticmethod
    def _is_not_synced(source_model: SourceModel, synchronized_at: datetime) -> bool:
        if source_model.last_successful_sync_at is None:
            return True
        next_sync = source_model.last_successful_sync_at + timedelta(
            seconds=source_model.interval_seconds
        )
        return synchronized_at >= next_sync

    @staticmethod
    def _to_domain(source_model: SourceModel) -> Source:
        return Source(
            id=source_model.id,
            category=source_model.category,
            language=source_model.language,
            interval_seconds=source_model.interval_seconds,
            enabled=source_model.enabled,
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
