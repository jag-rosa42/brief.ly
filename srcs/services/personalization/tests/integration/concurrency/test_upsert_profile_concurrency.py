"""
Concurrency test for PUT /me/profile.

The two requests run in independent database transactions (``concurrent_clients``),
so the data is really committed: the test deletes it at the end.
"""

import threading
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, delete
from sqlalchemy.orm import Session

from src.api.dependencies import ACCOUNT_ID_HEADER_NAME
from src.api.dependencies.topic_catalog import get_topic_catalog
from src.infrastructure.database.models.profile import Profile as ProfileModel
from src.main import app
from tests.fakes import FakeTopicCatalog
from tests.routes import ME_PROFILE


@pytest.fixture
def account_id(engine: Engine) -> Generator[UUID]:
    account_id: UUID = uuid4()
    try:
        yield account_id
    finally:
        # ON DELETE CASCADE removes the profile's interests too.
        with Session(engine) as session:
            session.execute(
                delete(ProfileModel).where(ProfileModel.account_id == account_id)
            )
            session.commit()


@pytest.fixture
def topic_catalog() -> Generator[FakeTopicCatalog]:
    catalog = FakeTopicCatalog(["science"])
    app.dependency_overrides[get_topic_catalog] = lambda: catalog
    try:
        yield catalog
    finally:
        # concurrent_clients only removes its own override.
        app.dependency_overrides.pop(get_topic_catalog, None)


def test_two_first_puts_at_the_same_time_create_the_profile_once(
    concurrent_clients: tuple[TestClient, TestClient],
    account_id: UUID,
    topic_catalog: FakeTopicCatalog,
) -> None:
    # timeout: never hang the test suite if one thread fails early.
    start_together = threading.Barrier(2, timeout=5)

    def first_put(client: TestClient) -> int:
        start_together.wait()
        response = client.put(
            ME_PROFILE,
            headers={ACCOUNT_ID_HEADER_NAME: str(account_id)},
            json={"name": "John", "topic_ids": ["science"]},
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        status_codes = list(pool.map(first_put, concurrent_clients))

    assert sorted(status_codes) == [200, 201]
