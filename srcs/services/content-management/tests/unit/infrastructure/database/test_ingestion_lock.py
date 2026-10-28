from unittest.mock import Mock

from src.infrastructure.database.ingestion_lock import PostgresIngestionLock


def test_reports_whether_the_transaction_lock_was_acquired() -> None:
    session = Mock()
    session.scalar.side_effect = [True, False]
    lock = PostgresIngestionLock(session)

    assert lock.try_acquire()
    assert not lock.try_acquire()
    assert session.scalar.call_count == 2
