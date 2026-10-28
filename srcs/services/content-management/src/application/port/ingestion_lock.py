from typing import Protocol


class IngestionLock(Protocol):
    """Coordinates ingestion runs across all service processes."""

    def try_acquire(self) -> bool:
        """Acquire the lock for the current transaction without waiting."""
        ...
