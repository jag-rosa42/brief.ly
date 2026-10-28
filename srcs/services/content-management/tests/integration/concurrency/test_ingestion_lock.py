import pytest
from sqlalchemy import Engine

from src.infrastructure.database.ingestion_lock import PostgresIngestionLock


@pytest.mark.integration
def test_only_one_session_can_hold_the_ingestion_lock(engine: Engine) -> None:
    holder = PostgresIngestionLock(engine)
    contender = PostgresIngestionLock(engine)
    try:
        assert holder.try_acquire()
        assert not contender.try_acquire()

        holder.release()

        assert contender.try_acquire()
    finally:
        holder.release()
        contender.release()
