"""The service token checks of the /internal routes (ADR-0008).

The other API tests send a token with every scope (tests/fixtures/auth.py);
these check the refusals. The route's own dependencies (database, use case)
are never reached: the token check runs first.
"""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from shared_auth.testing import FakeTokenIssuer

from src.main import app
from tests import routes
from tests.fixtures.auth import ALL_SCOPES, SERVICE_AUDIENCE

SUMMARY_BODY = {
    "text": "A summary.",
    "llm_model": "gemma2:2b",
    "generation_duration_ms": 1,
}

# (method, path, body, the scope the route needs)
PROTECTED_ROUTES = [
    pytest.param("GET", routes.TOPICS, None, "topics:read", id="list-topics"),
    pytest.param(
        "PUT",
        routes.topic_summary("technology"),
        SUMMARY_BODY,
        "summaries:write",
        id="put-topic-summary",
    ),
    pytest.param("GET", routes.ARTICLES, None, "articles:read", id="list-articles"),
    pytest.param(
        "GET", routes.article_detail(uuid4()), None, "articles:read", id="get-article"
    ),
    pytest.param(
        "PUT",
        routes.article_summary(uuid4()),
        {**SUMMARY_BODY, "rejected": False, "quality_comment": "Complete"},
        "summaries:write",
        id="put-article-summary",
    ),
]


@pytest.fixture
def anonymous_client() -> TestClient:
    return TestClient(app)


@pytest.mark.parametrize(("method", "path", "body", "scope"), PROTECTED_ROUTES)
def test_refuses_a_request_without_token(
    anonymous_client: TestClient,
    method: str,
    path: str,
    body: dict[str, object] | None,
    scope: str,
) -> None:
    response = anonymous_client.request(method, path, json=body)

    assert response.status_code == 401


@pytest.mark.parametrize(("method", "path", "body", "scope"), PROTECTED_ROUTES)
def test_refuses_a_token_without_the_route_scope(
    anonymous_client: TestClient,
    token_issuer: FakeTokenIssuer,
    method: str,
    path: str,
    body: dict[str, object] | None,
    scope: str,
) -> None:
    other_scopes = [other for other in ALL_SCOPES if other != scope]
    token = token_issuer.service_token(
        "personalization", audience=SERVICE_AUDIENCE, scopes=other_scopes
    )

    response = anonymous_client.request(
        method, path, json=body, headers=token_issuer.bearer(token)
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "INSUFFICIENT_SCOPE"


def test_refuses_a_token_addressed_to_another_service(
    anonymous_client: TestClient, token_issuer: FakeTokenIssuer
) -> None:
    token = token_issuer.service_token(
        "morning-briefing",
        audience="transcendence:personalization",
        scopes=ALL_SCOPES,
    )

    response = anonymous_client.get(routes.TOPICS, headers=token_issuer.bearer(token))

    assert response.status_code == 401
