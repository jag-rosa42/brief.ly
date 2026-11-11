"""
Public API documentation (ADR-0009): the per-service document, and the two
ready-made public scope dependencies.

Each test builds a small app with neutral paths, like tests/fixtures/http.py.
"""

from typing import Any

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from shared_errors import register_shared_exception_handlers

from shared_auth.api.dependencies import PublicApiReaderDep, PublicApiWriterDep
from shared_auth.api.installation import install_authentication
from shared_auth.api.public_docs import (
    API_KEY_HEADER_NAME,
    API_KEY_SECURITY_SCHEME,
    KEY_RATE_LIMIT_PER_SECOND,
    PUBLIC_API_RESPONSES,
    PUBLIC_DOCS_PATH,
    RATE_LIMITS_DESCRIPTION,
    build_public_openapi,
    install_public_openapi,
    public_openapi_path,
)
from shared_auth.infrastructure.settings import AuthSettings
from tests.fixtures.factory import PUBLIC_API_AUDIENCE
from tests.fixtures.http import bearer, error_code
from tests.fixtures.security import TokenFactory

SERVICE_NAME: str = "example-service"
SERVICE_DESCRIPTION: str = "Example resources."


def build_public_router() -> APIRouter:
    """Two public routes: one that reads, one that writes."""
    router = APIRouter(prefix="/public/v1", responses=PUBLIC_API_RESPONSES)

    @router.get("/resources")
    def read_resources(user: PublicApiReaderDep) -> dict[str, str]:
        return {"account_id": str(user.account_id)}

    @router.put("/resources")
    def write_resources(user: PublicApiWriterDep) -> dict[str, str]:
        return {"account_id": str(user.account_id)}

    return router


@pytest.fixture
def app(auth_settings: AuthSettings) -> FastAPI:
    """A service with a frontend route, an internal route and public routes."""
    app = FastAPI()
    register_shared_exception_handlers(app)
    install_authentication(app, auth_settings, public_api=True)

    @app.get("/frontend-resource")
    def frontend_resource() -> dict[str, str]:
        return {}

    @app.get("/internal/v1/resource")
    def internal_resource() -> dict[str, str]:
        return {}

    public_router = build_public_router()
    app.include_router(public_router)
    install_public_openapi(
        app, public_router, service_name=SERVICE_NAME, description=SERVICE_DESCRIPTION
    )
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture
def document(client: TestClient) -> dict[str, Any]:
    return client.get(public_openapi_path(SERVICE_NAME)).json()


def public_token(make_token: TokenFactory, scope: str) -> dict[str, str]:
    return bearer(make_token(overrides={"aud": PUBLIC_API_AUDIENCE, "scope": scope}))


class TestPublicOpenApiDocument:
    def test_is_served_at_the_service_path(self, client: TestClient) -> None:
        response: Response = client.get("/public/v1/openapi/example-service.json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_holds_only_the_public_routes(self, document: dict[str, Any]) -> None:
        assert set(document["paths"]) == {"/public/v1/resources"}
        assert set(document["paths"]["/public/v1/resources"]) == {"get", "put"}

    def test_declares_the_api_key_header(self, document: dict[str, Any]) -> None:
        scheme = document["components"]["securitySchemes"][API_KEY_SECURITY_SCHEME]
        assert scheme["type"] == "apiKey"
        assert scheme["in"] == "header"
        assert scheme["name"] == API_KEY_HEADER_NAME == "X-API-Key"
        assert document["security"] == [{API_KEY_SECURITY_SCHEME: []}]

    def test_offers_the_key_only_never_the_bearer_token(
        self, document: dict[str, Any]
    ) -> None:
        # The routes verify a Bearer token, so FastAPI documents HTTPBearer on
        # each one. A program never sends it (the gateway does): Swagger UI
        # must only ask for the key.
        assert list(document["components"]["securitySchemes"]) == [
            API_KEY_SECURITY_SCHEME
        ]
        for operation in document["paths"]["/public/v1/resources"].values():
            assert "security" not in operation

    def test_every_route_documents_the_gateway_errors(
        self, document: dict[str, Any]
    ) -> None:
        for operation in document["paths"]["/public/v1/resources"].values():
            assert {"401", "403", "429"} <= set(operation["responses"])

    def test_the_429_documents_the_limits_and_its_headers(
        self, document: dict[str, Any]
    ) -> None:
        too_many: dict[str, Any] = document["paths"]["/public/v1/resources"]["get"][
            "responses"
        ]["429"]

        assert (
            f"{KEY_RATE_LIMIT_PER_SECOND} requests per second per API key"
            in (too_many["description"])
        )
        assert too_many["headers"]["Retry-After"]["schema"] == {"type": "integer"}
        assert "X-RateLimit-Limit-Per-Key" in too_many["headers"]
        # Traefik's own plain-text answer: no body schema to document.
        assert "content" not in too_many

    def test_states_the_rate_limits_under_the_service_description(
        self, document: dict[str, Any]
    ) -> None:
        assert document["info"]["description"] == (
            f"{SERVICE_DESCRIPTION}\n\n{RATE_LIMITS_DESCRIPTION}"
        )

    def test_states_the_rate_limits_without_a_service_description(self) -> None:
        document: dict[str, Any] = build_public_openapi(
            build_public_router(), title="Example"
        )

        assert document["info"]["description"] == RATE_LIMITS_DESCRIPTION

    def test_is_not_listed_in_the_service_own_document(self, app: FastAPI) -> None:
        # The service's own /openapi.json (never routed by the gateway) lists
        # its real routes, not the document routes.
        assert public_openapi_path(SERVICE_NAME) not in app.openapi()["paths"]
        assert PUBLIC_DOCS_PATH not in app.openapi()["paths"]

    def test_a_non_public_route_stops_the_service_at_startup(self) -> None:
        router = APIRouter()

        @router.get("/internal/v1/secret")
        def secret() -> dict[str, str]:
            return {}

        with pytest.raises(ValueError, match="not a public route"):
            build_public_openapi(router, title="Example")

    def test_a_non_public_route_in_an_included_router_is_found(self) -> None:
        # Since FastAPI 0.143 an included router stays a wrapper: its routes
        # are not listed in router.routes, but the check must still see them.
        inner = APIRouter(prefix="/internal/v1")

        @inner.get("/secret")
        def secret() -> dict[str, str]:
            return {}

        outer = APIRouter()
        outer.include_router(inner)

        with pytest.raises(ValueError, match="/internal/v1/secret"):
            build_public_openapi(outer, title="Example")

    def test_a_route_named_like_the_prefix_is_not_public(self) -> None:
        # "/public/v10" starts with "/public/v1" but is not under it.
        router = APIRouter()

        @router.get("/public/v10/resources")
        def resources() -> dict[str, str]:
            return {}

        with pytest.raises(ValueError, match="not a public route"):
            build_public_openapi(router, title="Example")


class TestPublicApiScopeDependencies:
    def test_reader_accepts_a_read_token(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        response: Response = client.get(
            "/public/v1/resources", headers=public_token(make_token, "read")
        )

        assert response.status_code == 200

    def test_writer_refuses_a_read_only_token(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        response: Response = client.put(
            "/public/v1/resources", headers=public_token(make_token, "read")
        )

        assert response.status_code == 403
        assert error_code(response) == "INSUFFICIENT_SCOPE"

    def test_writer_accepts_a_write_token(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        response: Response = client.put(
            "/public/v1/resources", headers=public_token(make_token, "read write")
        )

        assert response.status_code == 200

    def test_a_browser_token_is_refused(
        self, client: TestClient, make_token: TokenFactory
    ) -> None:
        # Default token: a browser access token, another audience.
        response: Response = client.get(
            "/public/v1/resources", headers=bearer(make_token())
        )

        assert response.status_code == 401
