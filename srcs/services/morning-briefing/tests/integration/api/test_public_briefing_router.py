"""GET /public/v1/morning-briefing (ADR-0009) and the public document.

Real public API tokens (FakeTokenIssuer, the shape the gateway gets from
Identity) checked by shared_auth's real code. The three clients are the
fakes of tests/fakes.py, like in test_briefing_router.py: the use case is
the frontend route's one. What is new here is who may call, with which
scope, which token goes to Personalization, and the public document.
"""

from collections.abc import Generator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_auth.testing import FakeTokenIssuer
from shared_errors import ErrorResponse

from src.api.dependencies.briefing import (
    get_article_catalog,
    get_profile_reader,
    get_topic_catalog,
)
from src.domain.entities.profile import Profile
from src.domain.entities.topic import Topic
from src.main import app
from tests.fakes import FakeArticleCatalog, FakeProfileReader, FakeTopicCatalog
from tests.fixtures.auth import SERVICE_AUDIENCE
from tests.routes import BRIEFING, PUBLIC_BRIEFING, PUBLIC_OPENAPI

PROFILE = Profile(name="Kate", topic_ids=("technology",), saved_article_ids=())
TOPICS = [Topic(id="technology", summary="Tech news of the day.")]


def error_code(response: Response) -> str:
    return ErrorResponse.model_validate(response.json()).error.code


@pytest.fixture
def profile_reader() -> FakeProfileReader:
    return FakeProfileReader(PROFILE)


@pytest.fixture
def client(
    token_issuer: FakeTokenIssuer, profile_reader: FakeProfileReader
) -> Generator[TestClient]:
    """TestClient without database (shadows the database client)."""
    app.dependency_overrides[get_profile_reader] = lambda: profile_reader
    app.dependency_overrides[get_topic_catalog] = lambda: FakeTopicCatalog(TOPICS)
    app.dependency_overrides[get_article_catalog] = lambda: FakeArticleCatalog([])
    token_issuer.override_authenticator(
        app, service_audience=SERVICE_AUDIENCE, public_api=True
    )
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def key(token_issuer: FakeTokenIssuer, account_id: UUID, *scopes: str) -> str:
    """The token the gateway forwards for a key with these scopes."""
    return token_issuer.public_api_token(account_id, scopes=scopes)


class TestPublicBriefing:
    def test_returns_the_briefing_with_a_read_key(
        self, client: TestClient, token_issuer: FakeTokenIssuer
    ) -> None:
        token: str = key(token_issuer, uuid4(), "read")

        response: Response = client.get(
            PUBLIC_BRIEFING, headers=token_issuer.bearer(token)
        )

        assert response.status_code == 200
        assert response.json()["profile"]["name"] == "Kate"
        assert response.json()["topic_clusters"][0]["topic_id"] == "technology"

    def test_forwards_the_public_api_token_to_personalization(
        self,
        client: TestClient,
        token_issuer: FakeTokenIssuer,
        profile_reader: FakeProfileReader,
    ) -> None:
        # Personalization's internal route accepts it (forwarded user token).
        token: str = key(token_issuer, uuid4(), "read")

        client.get(PUBLIC_BRIEFING, headers=token_issuer.bearer(token))

        assert profile_reader.tokens == [token]

    def test_needs_read(self, client: TestClient, token_issuer: FakeTokenIssuer) -> None:
        token: str = key(token_issuer, uuid4(), "write")

        response: Response = client.get(
            PUBLIC_BRIEFING, headers=token_issuer.bearer(token)
        )

        assert response.status_code == 403
        assert error_code(response) == "INSUFFICIENT_SCOPE"

    def test_refuses_a_browser_token(
        self, client: TestClient, token_issuer: FakeTokenIssuer
    ) -> None:
        token: str = token_issuer.user_token(uuid4())

        response: Response = client.get(
            PUBLIC_BRIEFING, headers=token_issuer.bearer(token)
        )

        assert response.status_code == 401

    def test_refuses_a_request_without_a_token(self, client: TestClient) -> None:
        response: Response = client.get(PUBLIC_BRIEFING)

        assert response.status_code == 401
        assert error_code(response) == "INVALID_TOKEN"

    def test_a_public_api_token_never_opens_the_frontend_route(
        self, client: TestClient, token_issuer: FakeTokenIssuer
    ) -> None:
        token: str = key(token_issuer, uuid4(), "read")

        response: Response = client.get(BRIEFING, headers=token_issuer.bearer(token))

        assert response.status_code == 401


class TestPublicDocument:
    def test_holds_only_the_public_route(self, client: TestClient) -> None:
        response: Response = client.get(PUBLIC_OPENAPI)

        assert response.status_code == 200
        assert list(response.json()["paths"]) == ["/public/v1/morning-briefing"]

    def test_offers_the_api_key_only(self, client: TestClient) -> None:
        document: dict[str, Any] = client.get(PUBLIC_OPENAPI).json()

        schemes: dict[str, Any] = document["components"]["securitySchemes"]
        assert [scheme.get("name") for scheme in schemes.values()] == ["X-API-Key"]

    def test_documents_401_403_and_429(self, client: TestClient) -> None:
        document: dict[str, Any] = client.get(PUBLIC_OPENAPI).json()

        operation = document["paths"]["/public/v1/morning-briefing"]["get"]
        assert {"401", "403", "429"} <= set(operation["responses"])
