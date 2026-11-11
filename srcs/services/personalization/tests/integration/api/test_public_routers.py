"""The public routes (ADR-0009), the public document and the docs page.

Real public API tokens (FakeTokenIssuer, the shape the gateway gets from
Identity) checked by shared_auth's real code. The repositories, the unit of
work and the catalogs are in-memory fakes: the use cases are the frontend
routes' ones, already tested against PostgreSQL. What is new here is who may
call, with which scope, and what the public document contains.
"""

from collections.abc import Callable, Generator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_auth.api.installation import get_authenticator
from shared_auth.testing import FakeTokenIssuer
from shared_errors import ErrorResponse

from src.api.dependencies.article_catalog import get_article_catalog
from src.api.dependencies.database import get_unit_of_work
from src.api.dependencies.profile import get_profile_repository
from src.api.dependencies.saved_article import get_saved_article_repository
from src.api.dependencies.topic_catalog import get_topic_catalog
from src.domain.entities.article import Article
from src.domain.entities.profile import Profile
from src.main import app
from tests.fakes import (
    FakeArticleCatalog,
    FakeProfileRepository,
    FakeSavedArticleRepository,
    FakeTopicCatalog,
    FakeUnitOfWork,
)
from tests.fixtures.auth import SERVICE_AUDIENCE
from tests.routes import (
    ME_PROFILE,
    PUBLIC_DOCS,
    PUBLIC_ME_PROFILE,
    PUBLIC_ME_SAVED_ARTICLES,
    PUBLIC_OPENAPI,
    PUBLIC_TOPICS,
    public_me_saved_article,
)

TOPICS: list[str] = ["business", "science", "technology"]
ARTICLE = Article(
    article_id=uuid4(),
    title="An article",
    source="A publisher",
    topic_id="science",
    summary=None,
    url="https://example.com/article",
    read_time_minutes=4,
)

Headers = Callable[..., dict[str, str]]


def error_code(response: Response) -> str:
    return ErrorResponse.model_validate(response.json()).error.code


class TimestampedProfileRepository(FakeProfileRepository):
    """Sets created_at and updated_at like PostgreSQL does: the responses
    need them (ProfileResponse.from_domain)."""

    def add(self, profile: Profile) -> None:
        self._stamp(profile)
        super().add(profile)

    def upsert(self, profile: Profile) -> bool:
        self._stamp(profile)
        return super().upsert(profile)

    @staticmethod
    def _stamp(profile: Profile) -> None:
        now: datetime = datetime.now(UTC)
        profile.created_at = profile.created_at or now
        profile.updated_at = now


@pytest.fixture
def profiles() -> FakeProfileRepository:
    return TimestampedProfileRepository()


@pytest.fixture
def saved_articles() -> FakeSavedArticleRepository:
    return FakeSavedArticleRepository()


@pytest.fixture
def client(
    token_issuer: FakeTokenIssuer,
    profiles: FakeProfileRepository,
    saved_articles: FakeSavedArticleRepository,
) -> Generator[TestClient]:
    """TestClient with in-memory data (shadows the database client)."""
    app.dependency_overrides[get_profile_repository] = lambda: profiles
    app.dependency_overrides[get_saved_article_repository] = lambda: saved_articles
    app.dependency_overrides[get_unit_of_work] = FakeUnitOfWork
    app.dependency_overrides[get_topic_catalog] = lambda: FakeTopicCatalog(TOPICS)
    app.dependency_overrides[get_article_catalog] = lambda: FakeArticleCatalog([ARTICLE])
    token_issuer.override_authenticator(
        app, service_audience=SERVICE_AUDIENCE, public_api=True
    )
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def key(token_issuer: FakeTokenIssuer) -> Headers:
    """The Authorization header the gateway sends for a key with these scopes."""

    def build(account_id: UUID, *scopes: str) -> dict[str, str]:
        return token_issuer.bearer(
            token_issuer.public_api_token(account_id, scopes=scopes)
        )

    return build


@pytest.fixture
def account_id(profiles: FakeProfileRepository) -> UUID:
    """An account that already has a profile."""
    account_id: UUID = uuid4()
    profile = Profile.create(account_id=account_id, name="John", topic_ids=["science"])
    profiles.add(profile)
    return account_id


def public_routes() -> list[tuple[str, str]]:
    """(method, path) of every route under /public/v1, docs excluded.

    Read from the service's own OpenAPI document: it lists every route, and
    the docs routes are left out of it (include_in_schema=False).
    """
    routes: list[tuple[str, str]] = []
    for path, operations in app.openapi()["paths"].items():
        if path.startswith("/public/v1/"):
            concrete: str = path.replace("{article_id}", str(uuid4()))
            routes.extend((method.upper(), concrete) for method in operations)
    return routes


class TestEveryPublicRoute:
    def test_there_are_the_six_routes_of_the_contract(self) -> None:
        assert len(public_routes()) == 6

    @pytest.mark.parametrize(("method", "path"), public_routes())
    def test_refuses_a_browser_token(
        self,
        client: TestClient,
        token_issuer: FakeTokenIssuer,
        account_id: UUID,
        method: str,
        path: str,
    ) -> None:
        # Another audience: a browser token never opens the public API.
        headers = token_issuer.bearer(token_issuer.user_token(account_id))

        response: Response = client.request(method, path, headers=headers)

        assert response.status_code == 401

    @pytest.mark.parametrize(("method", "path"), public_routes())
    def test_refuses_a_request_without_a_token(
        self, client: TestClient, method: str, path: str
    ) -> None:
        response: Response = client.request(method, path)

        assert response.status_code == 401
        assert error_code(response) == "INVALID_TOKEN"

    def test_a_public_api_token_never_opens_a_frontend_route(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        response: Response = client.get(
            ME_PROFILE, headers=key(account_id, "read", "write")
        )

        assert response.status_code == 401


class TestPublicProfile:
    def test_get_returns_the_key_owner_profile(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        headers = key(account_id, "read")

        response: Response = client.get(PUBLIC_ME_PROFILE, headers=headers)

        assert response.status_code == 200
        assert response.json()["name"] == "John"

    def test_get_never_returns_another_account(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        response: Response = client.get(PUBLIC_ME_PROFILE, headers=key(uuid4(), "read"))

        assert response.status_code == 404

    def test_get_needs_read(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        response: Response = client.get(
            PUBLIC_ME_PROFILE, headers=key(account_id, "write")
        )

        assert response.status_code == 403
        assert error_code(response) == "INSUFFICIENT_SCOPE"

    def test_put_creates_then_updates(
        self, client: TestClient, key: Headers, profiles: FakeProfileRepository
    ) -> None:
        owner: UUID = uuid4()
        body: dict[str, Any] = {"name": "Jane", "topic_ids": ["business"]}

        created = client.put(PUBLIC_ME_PROFILE, json=body, headers=key(owner, "write"))
        updated = client.put(PUBLIC_ME_PROFILE, json=body, headers=key(owner, "write"))

        assert created.status_code == 201
        assert updated.status_code == 200
        assert profiles.find_by_id(owner) is not None

    def test_put_needs_write(
        self, client: TestClient, key: Headers, profiles: FakeProfileRepository
    ) -> None:
        owner: UUID = uuid4()
        body: dict[str, Any] = {"name": "Jane", "topic_ids": ["business"]}

        response = client.put(PUBLIC_ME_PROFILE, json=body, headers=key(owner, "read"))

        assert response.status_code == 403
        assert profiles.find_by_id(owner) is None


class TestPublicSavedArticles:
    def test_post_saves_then_get_lists_then_delete_removes(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        path: str = public_me_saved_article(ARTICLE.article_id)
        writer = key(account_id, "read", "write")

        saved: Response = client.post(path, headers=writer)
        listed: Response = client.get(PUBLIC_ME_SAVED_ARTICLES, headers=writer)
        deleted: Response = client.delete(path, headers=writer)
        after: Response = client.get(PUBLIC_ME_SAVED_ARTICLES, headers=writer)

        assert saved.status_code == 201
        assert saved.json()["article_id"] == str(ARTICLE.article_id)
        assert [item["article_id"] for item in listed.json()["items"]] == [
            str(ARTICLE.article_id)
        ]
        assert deleted.status_code == 204
        assert after.json() == {"items": []}

    def test_post_needs_write(
        self,
        client: TestClient,
        key: Headers,
        account_id: UUID,
        saved_articles: FakeSavedArticleRepository,
    ) -> None:
        response: Response = client.post(
            public_me_saved_article(ARTICLE.article_id), headers=key(account_id, "read")
        )

        assert response.status_code == 403
        assert saved_articles.count_for_account(account_id) == 0

    def test_delete_needs_write(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        response: Response = client.delete(
            public_me_saved_article(ARTICLE.article_id), headers=key(account_id, "read")
        )

        assert response.status_code == 403

    def test_get_needs_read(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        response: Response = client.get(
            PUBLIC_ME_SAVED_ARTICLES, headers=key(account_id, "write")
        )

        assert response.status_code == 403


class TestPublicTopics:
    def test_get_returns_the_catalog(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        response: Response = client.get(PUBLIC_TOPICS, headers=key(account_id, "read"))

        assert response.status_code == 200
        assert [item["id"] for item in response.json()["items"]] == TOPICS

    def test_get_needs_read(
        self, client: TestClient, key: Headers, account_id: UUID
    ) -> None:
        response: Response = client.get(PUBLIC_TOPICS, headers=key(account_id, "write"))

        assert response.status_code == 403


class TestPublicDocumentation:
    def test_the_document_holds_only_the_public_routes(self, client: TestClient) -> None:
        response: Response = client.get(PUBLIC_OPENAPI)

        assert response.status_code == 200
        assert set(response.json()["paths"]) == {
            "/public/v1/me/profile",
            "/public/v1/me/saved-articles",
            "/public/v1/me/saved-articles/{article_id}",
            "/public/v1/topics",
        }

    def test_the_document_names_the_api_key_header(self, client: TestClient) -> None:
        document: dict[str, Any] = client.get(PUBLIC_OPENAPI).json()

        schemes: dict[str, Any] = document["components"]["securitySchemes"]
        # Only the key: a program never sends the Bearer token itself.
        assert [scheme.get("name") for scheme in schemes.values()] == ["X-API-Key"]

    def test_every_route_documents_401_403_and_429(self, client: TestClient) -> None:
        document: dict[str, Any] = client.get(PUBLIC_OPENAPI).json()

        for operations in document["paths"].values():
            for operation in operations.values():
                assert {"401", "403", "429"} <= set(operation["responses"])

    def test_the_docs_page_lists_both_services(self, client: TestClient) -> None:
        response: Response = client.get(PUBLIC_DOCS)

        assert response.status_code == 200
        assert "/public/v1/openapi/personalization.json" in response.text
        assert "/public/v1/openapi/morning-briefing.json" in response.text

    def test_documentation_needs_no_token(self, client: TestClient) -> None:
        # The gateway routes these paths without ForwardAuth.
        assert client.get(PUBLIC_OPENAPI).status_code == 200
        assert client.get(PUBLIC_DOCS).status_code == 200

    def test_the_service_own_document_still_lists_every_route(self) -> None:
        # /openapi.json (never routed by the gateway) is unchanged: the team
        # still sees every route there.
        paths = app.openapi()["paths"]
        assert "/me/profile" in paths
        assert "/public/v1/me/profile" in paths


def test_no_authenticator_override_leaks() -> None:
    # The client fixture cleans up after itself.
    assert get_authenticator not in app.dependency_overrides
