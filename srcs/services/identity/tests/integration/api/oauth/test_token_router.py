"""POST /internal/v1/oauth/token through the whole stack.

Real registry, real use case, real JWT signing. Only the secrets folder is
replaced by a temporary one, so the test doesn't depend on shared/secrets.
"""

import base64
from collections.abc import Generator
from pathlib import Path
from typing import Any

import jwt
import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import ErrorResponse

from src.api.dependencies.oauth import (
    get_client_secret_verifier,
    get_service_client_registry,
)
from src.infrastructure.oauth.client_secret_verifier import (
    SecretFileClientSecretVerifier,
)
from src.infrastructure.security.settings import security_settings
from src.main import app
from tests import routes

CLIENT_ID: str = "personalization"
CLIENT_SECRET: str = "personalization-test-secret"
CONTENT_MANAGEMENT: str = "transcendence:content-management"


def basic(
    client_id: str = CLIENT_ID, client_secret: str = CLIENT_SECRET
) -> dict[str, str]:
    credentials: bytes = f"{client_id}:{client_secret}".encode()
    return {"Authorization": f"Basic {base64.b64encode(credentials).decode()}"}


def token_form(**overrides: str) -> dict[str, str]:
    form: dict[str, str] = {
        "grant_type": "client_credentials",
        "audience": CONTENT_MANAGEMENT,
        "scope": "topics:read",
    }
    form.update(overrides)
    return form


def error_code(response: Response) -> str:
    return ErrorResponse.model_validate(response.json()).error.code


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient]:
    """TestClient without database: the token endpoint doesn't use it."""
    (tmp_path / "personalization_client_secret").write_text(CLIENT_SECRET)
    app.dependency_overrides[get_client_secret_verifier] = lambda: (
        SecretFileClientSecretVerifier(
            secrets_dir=tmp_path,
            known_client_ids=get_service_client_registry().client_ids(),
        )
    )
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_client_secret_verifier, None)


class TestTokenEndpointSuccess:
    def test_returns_a_bearer_token_response(self, client: TestClient) -> None:
        response: Response = client.post(
            routes.OAUTH_TOKEN, headers=basic(), data=token_form()
        )

        assert response.status_code == 200
        body: dict[str, Any] = response.json()
        assert body["token_type"] == "Bearer"
        assert body["expires_in"] == security_settings.SERVICE_TOKEN_EXPIRE_MINUTES * 60
        assert body["access_token"]

    def test_the_token_is_a_service_token_for_the_audience(
        self, client: TestClient
    ) -> None:
        response: Response = client.post(
            routes.OAUTH_TOKEN,
            headers=basic(),
            data=token_form(scope="topics:read articles:read"),
        )

        claims: dict[str, Any] = jwt.decode(
            response.json()["access_token"],
            security_settings.JWT_PUBLIC_KEY,
            algorithms=["RS256"],
            audience=CONTENT_MANAGEMENT,
            issuer=security_settings.JWT_ISSUER,
        )
        assert claims["sub"] == "service:personalization"
        assert claims["type"] == "service"
        assert claims["scope"] == "articles:read topics:read"

    def test_forbids_caching_the_response(self, client: TestClient) -> None:
        response: Response = client.post(
            routes.OAUTH_TOKEN, headers=basic(), data=token_form()
        )

        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Pragma"] == "no-cache"

    def test_is_served_under_internal_v1(self) -> None:
        assert routes.OAUTH_TOKEN == "/internal/v1/oauth/token"


class TestTokenEndpointClientAuthentication:
    @pytest.mark.parametrize(
        "headers",
        [
            pytest.param({}, id="no Authorization header"),
            pytest.param({"Authorization": "Bearer abc"}, id="not Basic"),
            pytest.param({"Authorization": "Basic"}, id="Basic without credentials"),
            pytest.param({"Authorization": "Basic not-base64!"}, id="not base64"),
            pytest.param(
                {"Authorization": f"Basic {base64.b64encode(b'no-colon').decode()}"},
                id="no colon",
            ),
            pytest.param(basic(client_secret="wrong-secret"), id="wrong secret"),
            pytest.param(basic(client_id="unknown"), id="unknown client"),
        ],
    )
    def test_returns_401_invalid_client(
        self, client: TestClient, headers: dict[str, str]
    ) -> None:
        response: Response = client.post(
            routes.OAUTH_TOKEN, headers=headers, data=token_form()
        )

        assert response.status_code == 401
        assert error_code(response) == "INVALID_CLIENT"
        assert response.headers["WWW-Authenticate"] == "Basic"

    def test_unknown_client_and_wrong_secret_get_the_same_answer(
        self, client: TestClient
    ) -> None:
        unknown: Response = client.post(
            routes.OAUTH_TOKEN, headers=basic(client_id="unknown"), data=token_form()
        )
        wrong: Response = client.post(
            routes.OAUTH_TOKEN, headers=basic(client_secret="wrong"), data=token_form()
        )

        assert unknown.json() == wrong.json()


class TestTokenEndpointRequest:
    def test_returns_400_for_another_grant_type(self, client: TestClient) -> None:
        response: Response = client.post(
            routes.OAUTH_TOKEN, headers=basic(), data=token_form(grant_type="password")
        )

        assert response.status_code == 400
        assert error_code(response) == "UNSUPPORTED_GRANT_TYPE"

    @pytest.mark.parametrize(
        ("audience", "scope"),
        [
            pytest.param(CONTENT_MANAGEMENT, "summaries:write", id="scope not allowed"),
            pytest.param(
                CONTENT_MANAGEMENT,
                "topics:read summaries:write",
                id="one scope not allowed",
            ),
            pytest.param(CONTENT_MANAGEMENT, "", id="empty scope"),
            pytest.param(
                "transcendence:identity", "topics:read", id="audience not allowed"
            ),
        ],
    )
    def test_returns_400_invalid_scope(
        self, client: TestClient, audience: str, scope: str
    ) -> None:
        response: Response = client.post(
            routes.OAUTH_TOKEN,
            headers=basic(),
            data=token_form(audience=audience, scope=scope),
        )

        assert response.status_code == 400
        assert error_code(response) == "INVALID_SCOPE"

    def test_returns_400_invalid_scope_without_a_scope_field(
        self, client: TestClient
    ) -> None:
        form: dict[str, str] = token_form()
        del form["scope"]

        response: Response = client.post(routes.OAUTH_TOKEN, headers=basic(), data=form)

        assert response.status_code == 400
        assert error_code(response) == "INVALID_SCOPE"

    def test_returns_422_without_a_grant_type(self, client: TestClient) -> None:
        form: dict[str, str] = token_form()
        del form["grant_type"]

        response: Response = client.post(routes.OAUTH_TOKEN, headers=basic(), data=form)

        assert response.status_code == 422
        assert error_code(response) == "VALIDATION_ERROR"

    def test_refuses_a_json_body(self, client: TestClient) -> None:
        # RFC 6749 §4.4.2: the parameters are a form.
        response: Response = client.post(
            routes.OAUTH_TOKEN, headers=basic(), json=token_form()
        )

        assert response.status_code == 422
