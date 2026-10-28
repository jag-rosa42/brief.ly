from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.infrastructure.database.ingestion_lock import PostgresIngestionLock


def test_holds_the_session_lock_until_it_is_released() -> None:
    engine = Mock()
    connection = engine.connect.return_value
    connection.scalar.side_effect = [True, True]
    lock = PostgresIngestionLock(engine)

    assert lock.try_acquire()
    connection.commit.assert_called_once_with()
    connection.close.assert_not_called()

    lock.release()

    assert connection.scalar.call_count == 2
    assert connection.commit.call_count == 2
    connection.close.assert_called_once_with()


def test_closes_the_connection_when_the_lock_is_unavailable() -> None:
    engine = Mock()
    connection = engine.connect.return_value
    connection.scalar.return_value = False
    lock = PostgresIngestionLock(engine)

    assert not lock.try_acquire()

    connection.commit.assert_called_once_with()
    connection.close.assert_called_once_with()
    lock.release()
    assert connection.close.call_count == 1


def test_invalidates_the_connection_when_unlocking_fails() -> None:
    engine = Mock()
    connection = engine.connect.return_value
    connection.scalar.side_effect = [True, SQLAlchemyError("unlock failed")]
    lock = PostgresIngestionLock(engine)
    assert lock.try_acquire()

    with pytest.raises(SQLAlchemyError, match="unlock failed"):
        lock.release()

    connection.invalidate.assert_called_once_with()
    connection.close.assert_called_once_with()
