from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.infrastructure.database.models import SourceModel
from src.infrastructure.database.repositories import SqlAlchemySourceRepository


@pytest.mark.integration
def test_source_becomes_due_after_thirty_minutes(db_session: Session) -> None:
    source = db_session.scalar(
        select(SourceModel).where(SourceModel.category == "business")
    )
    assert source is not None
    synchronized_at = datetime(2026, 10, 26, 10, tzinfo=UTC)
    repository = SqlAlchemySourceRepository(db_session)

    repository.update_last_successful_sync(source.id, synchronized_at)
    repository.commit()
    db_session.expire_all()

    persisted_source = db_session.get(SourceModel, source.id)
    assert persisted_source is not None
    assert persisted_source.last_successful_sync_at is not None
    assert persisted_source.last_successful_sync_at.utcoffset() == timedelta(0)
    assert source.id not in {
        due.id for due in repository.list_due(synchronized_at + timedelta(minutes=29))
    }
    assert source.id in {
        due.id for due in repository.list_due(synchronized_at + timedelta(minutes=30))
    }
