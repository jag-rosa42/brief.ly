from collections.abc import Callable
from types import TracebackType
from typing import Self

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.exception import DomainError, EmailAlreadyRegisteredError

_UNIQUE_CONSTRAINT_ERRORS: dict[str, Callable[[], DomainError]] = {
    "uq_accounts_email": EmailAlreadyRegisteredError,
}


def _raise_domain_error_if_known(exc: SQLAlchemyError) -> None:
    """Raise the domain error mapped to a violated unique constraint.

    Returns without raising for any other error, so the caller re-raises
    the original SQLAlchemy exception.
    """
    if not isinstance(exc, IntegrityError):
        return
    # psycopg 3 exposes the violated constraint name on exc.orig.diag.
    diag = getattr(exc.orig, "diag", None)
    constraint_name: str | None = getattr(diag, "constraint_name", None)
    domain_error = _UNIQUE_CONSTRAINT_ERRORS.get(constraint_name or "")
    if domain_error is not None:
        raise domain_error() from exc


class SqlAlchemyUnitOfWork:
    """UnitOfWork backed by the request's SQLAlchemy Session.

    The repositories used together with this UnitOfWork MUST be built on
    the same Session (see src/api/dependencies/database.py). Otherwise
    commit() would not include their changes.
    """

    def __init__(self, session: Session) -> None:
        self._session: Session = session

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        # Always roll back, never commit here: a use case must call commit()
        # explicitly. Forgetting it discards the changes instead of saving
        # half-finished work.
        #
        # - After a successful commit(): no transaction is open anymore, so
        #   this does nothing (no ROLLBACK reaches the database).
        # - On an exception: undoes what was not committed and releases the
        #   SELECT ... FOR UPDATE row locks. Returning None lets the
        #   exception propagate.
        self._session.rollback()

    def flush(self) -> None:
        """Send staged changes to the database without committing them.

        Needed when a later statement of the same transaction depends on
        rows that are not committed yet (e.g. a foreign key).
        """
        try:
            self._session.flush()
        except SQLAlchemyError as exc:
            self._session.rollback()
            _raise_domain_error_if_known(exc)
            raise

    def commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError as exc:
            self._session.rollback()
            _raise_domain_error_if_known(exc)
            raise

    def rollback(self) -> None:
        self._session.rollback()
