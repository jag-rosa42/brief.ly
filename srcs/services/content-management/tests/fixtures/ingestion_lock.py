import pytest


class FakeIngestionLock:
    def __init__(self, acquired: bool = True) -> None:
        self.acquired = acquired
        self.acquire_count = 0
        self.release_count = 0

    def try_acquire(self) -> bool:
        self.acquire_count += 1
        return self.acquired

    def release(self) -> None:
        self.release_count += 1


@pytest.fixture
def ingestion_lock() -> FakeIngestionLock:
    return FakeIngestionLock()
