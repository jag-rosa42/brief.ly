from typing import Protocol


class IngestionLock(Protocol):
    """Coordinates ingestion runs across all service processes."""

    def try_acquire(self) -> bool:
        """Acquire the lock for the ingestion run without waiting."""
        ...

    def release(self) -> None:
        """Release a previously acquired ingestion lock."""
        ...
