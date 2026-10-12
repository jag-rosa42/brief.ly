from types import TracebackType
from typing import Protocol, Self

# Based on this source: https://dev.to/manukanne/a-python-implementation-of-the-unit-of-work-and-repository-design-pattern-using-sqlmodel-3mb5

class UnitOfWork(Protocol):
    """One database transaction for the duration of a use case.

    Repositories only read and stage changes. The UnitOfWork is the only
    object allowed to make them permanent, all together or not at all:

        with self._uow:
            ...                  # read and stage changes through repositories
            self._uow.commit()   # make every staged change permanent at once

    Leaving the ``with`` block always rolls back whatever was not committed
    (a no-op after a successful commit). This also releases the row locks
    taken with SELECT ... FOR UPDATE.

    Only use cases call commit(). Repositories and domain entities never do.
    """
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def flush(self) -> None:
        """Send staged changes to the database without committing them.

        Needed when a later statement of the same transaction depends on
        rows that are not committed yet (e.g. a foreign key).
        """
        ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...