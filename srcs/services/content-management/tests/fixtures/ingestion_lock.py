import pytest


class FakeIngestionLock:
    def __init__(self, acquired: bool = True) -> None:
        self.acquired = acquired
        self.acquire_count = 0

    def try_acquire(self) -> bool:
        self.acquire_count += 1
        return self.acquired


@pytest.fixture
def ingestion_lock() -> FakeIngestionLock:
    return FakeIngestionLock()
