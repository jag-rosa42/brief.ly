from sqlalchemy import Engine, func, select
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

# Two stable signed 32-bit keys identify the service-wide ingestion lock.
_INGESTION_LOCK_NAMESPACE = 0x434D
_INGESTION_LOCK_RESOURCE = 0x494E4745


class PostgresIngestionLock:
    """Non-blocking session-scoped PostgreSQL advisory lock."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._connection: Connection | None = None

    def try_acquire(self) -> bool:
        if self._connection is not None:
            raise RuntimeError("ingestion lock is already acquired")

        connection = self._engine.connect()
        try:
            statement = select(
                func.pg_try_advisory_lock(
                    _INGESTION_LOCK_NAMESPACE,
                    _INGESTION_LOCK_RESOURCE,
                )
            )
            acquired = bool(connection.scalar(statement))
            connection.commit()
        except SQLAlchemyError:
            connection.invalidate()
            connection.close()
            raise

        if not acquired:
            connection.close()
            return False

        self._connection = connection
        return True

    def release(self) -> None:
        connection = self._connection
        if connection is None:
            return

        self._connection = None
        try:
            statement = select(
                func.pg_advisory_unlock(
                    _INGESTION_LOCK_NAMESPACE,
                    _INGESTION_LOCK_RESOURCE,
                )
            )
            connection.scalar(statement)
            connection.commit()
        except SQLAlchemyError:
            # A session lock must never return to the pool after a failed unlock.
            connection.invalidate()
            raise
        finally:
            connection.close()
