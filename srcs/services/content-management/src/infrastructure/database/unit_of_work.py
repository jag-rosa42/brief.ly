from types import TracebackType
from typing import Self

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


class SqlAlchemyUnitOfWork:
    """Unit of Work backed by the request's SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._session.rollback()

    def flush(self) -> None:
        try:
            self._session.flush()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    def commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    def rollback(self) -> None:
        self._session.rollback()
