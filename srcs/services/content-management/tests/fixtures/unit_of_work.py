from types import TracebackType
from typing import Self

import pytest


class FakeUnitOfWork:
    """In-memory Unit of Work recording transaction operations."""

    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.flush_count = 0
        self._commit_error: Exception | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.rollback()

    def flush(self) -> None:
        self.flush_count += 1

    def commit(self) -> None:
        if self._commit_error is not None:
            raise self._commit_error
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def make_commit_raise(self, error: Exception) -> None:
        self._commit_error = error


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()
