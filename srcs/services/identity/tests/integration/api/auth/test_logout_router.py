from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response

from src.api.dependencies.account import get_logout_account
from src.main import app
from tests import routes
from tests.fixtures.sessions import FakeRefreshAccountSession

REFRESH_TOKEN: str = "current-refresh-token"


@pytest.fixture
def client() -> TestClient:
    """
    TestClient without database dependency overrides.

    This fixture shadows the conftest client fixture for tests
    that do not require database access.
    """
    return TestClient(app)


@pytest.fixture(autouse=True)
def use_logout_account() -> Generator:
    def _use(fake_use_case: FakeRefreshAccountSession) -> None:
        app.dependency_overrides[get_logout_account] = lambda: fake_use_case

    yield _use
    app.dependency_overrides.pop(get_logout_account, None)


class TestAuthLogoutRouter:
    def test_returns_204_without_a_body(
        self,
        client: TestClient,
        use_logout_account,
    ) -> None:
        fake = FakeRefreshAccountSession()
        use_logout_account(fake)

        response: Response = client.post(
            url=routes.LOGOUT,
            json={"refresh_token": REFRESH_TOKEN},
        )

        assert response.status_code == 204
        # response.content is returned as bytes.
        #  b"" is an empty bytes value
        assert response.content == b""
        assert fake._execute_called_with == REFRESH_TOKEN

    @pytest.mark.parametrize(
        "body",
        [
            {},
            {"refresh_token": None},
        ],
    )
    def test_returns_422_on_invalid_request_body(
        self,
        client: TestClient,
        body: dict,
    ) -> None:
        response: Response = client.post(
            url=routes.LOGOUT,
            json=body,
        )

        assert response.status_code == 422
