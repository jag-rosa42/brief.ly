from sqlalchemy import func, select
from sqlalchemy.orm import Session

# Two stable signed 32-bit keys identify the service-wide ingestion lock.
_INGESTION_LOCK_NAMESPACE = 0x434D
_INGESTION_LOCK_RESOURCE = 0x494E4745


class PostgresIngestionLock:
    """Non-blocking transaction-scoped PostgreSQL advisory lock."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def try_acquire(self) -> bool:
        statement = select(
            func.pg_try_advisory_xact_lock(
                _INGESTION_LOCK_NAMESPACE,
                _INGESTION_LOCK_RESOURCE,
            )
        )
        return bool(self._session.scalar(statement))
