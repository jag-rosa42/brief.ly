from types import TracebackType
from typing import Self

import pytest


class FakeUnitOfWork:
    """In-memory UnitOfWork that records what the use case asked for.

    Like the real one, leaving the ``with`` block always calls rollback().
    So in tests, assert on ``committed`` / ``commit_count``. ``rolled_back``
    only says the block was left, not that something went wrong.
    """

    def __init__(self) -> None:
        self.commit_count: int = 0
        self.rollback_count: int = 0
        self.flushed: bool = False
        self._failure_to_raise_on_commit: Exception | None = None

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
        self.flushed = True

    def commit(self) -> None:
        if self._failure_to_raise_on_commit is not None:
            raise self._failure_to_raise_on_commit
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    @property
    def committed(self) -> bool:
        return self.commit_count > 0

    @property
    def rolled_back(self) -> bool:
        return self.rollback_count > 0

    # Helper to simulate a failure at commit time
    # (e.g. the real UnitOfWork translating a unique violation).
    def make_commit_raise(self, exception: Exception) -> None:
        self._failure_to_raise_on_commit = exception


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()