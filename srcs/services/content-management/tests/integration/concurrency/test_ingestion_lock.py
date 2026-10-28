import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from src.infrastructure.database.ingestion_lock import PostgresIngestionLock


@pytest.mark.integration
def test_only_one_transaction_can_hold_the_ingestion_lock(engine: Engine) -> None:
    with Session(engine) as holder, Session(engine) as contender:
        assert PostgresIngestionLock(holder).try_acquire()
        assert not PostgresIngestionLock(contender).try_acquire()

        holder.rollback()

        assert PostgresIngestionLock(contender).try_acquire()
