"""
GET /briefing: the route, its authentication and its errors.

The three clients are replaced by the fakes of tests/fakes.py, so these tests
check the route itself: the response format of docs/api/03_morning-briefing.md,
the token forwarded to Personalization, and the status of each error.
"""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from shared_auth import TokenExpiredError
from shared_errors import ErrorResponse

from src.api.dependencies.briefing import (
    get_article_catalog,
    get_profile_reader,
    get_topic_catalog,
)
from src.domain.entities.profile import Profile
from src.domain.entities.topic import Topic
from src.main import app
from tests.fakes import (
    FakeArticleCatalog,
    FakeProfileReader,
    FakeTopicCatalog,
    article,
)
from tests.fixtures.auth import AuthHeaders
from tests.routes import BRIEFING

SAVED_ID = UUID("00000000-0000-0000-0000-000000000001")
TECH_ARTICLE_ID = UUID("00000000-0000-0000-0000-000000000002")

PROFILE = Profile(
    name="Kate",
    topic_ids=("technology", "science"),
    saved_article_ids=(SAVED_ID,),
)
TOPICS = [
    Topic(id="technology", summary="Tech news of the day."),
    Topic(id="science", summary=None),
]


def use_fakes(
    profile_reader: FakeProfileReader,
    topic_catalog: FakeTopicCatalog | None = None,
    article_catalog: FakeArticleCatalog | None = None,
) -> None:
    app.dependency_overrides[get_profile_reader] = lambda: profile_reader
    app.dependency_overrides[get_topic_catalog] = lambda: (
        topic_catalog or FakeTopicCatalog(TOPICS)
    )
    app.dependency_overrides[get_article_catalog] = lambda: (
        article_catalog or FakeArticleCatalog([article("technology", TECH_ARTICLE_ID)])
    )


@pytest.fixture
def headers(auth_headers: AuthHeaders) -> dict[str, str]:
    return auth_headers(uuid4())


def test_get_returns_the_briefing_in_the_contract_format(
    client: TestClient, headers: dict[str, str]
) -> None:
    use_fakes(FakeProfileReader(PROFILE))

    response = client.get(BRIEFING, headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "profile": {
            "name": "Kate",
            "topic_ids": ["technology", "science"],
            "saved_article_ids": [str(SAVED_ID)],
        },
        "topic_clusters": [
            {
                "topic_id": "technology",
                "summary": "Tech news of the day.",
                "articles": [
                    {
                        "article_id": str(TECH_ARTICLE_ID),
                        "title": "Article about technology",
                        "publisher_name": "TechDaily",
                        "url": "https://example.com/article",
                        "summary": None,
                        "read_time_minutes": 0,
                        "topic_id": "technology",
                    }
                ],
            },
            # No summary yet, no article: the cluster is still there.
            {"topic_id": "science", "summary": None, "articles": []},
        ],
    }


def test_get_forwards_the_user_token_to_personalization(
    client: TestClient, headers: dict[str, str]
) -> None:
    profile_reader = FakeProfileReader(PROFILE)
    use_fakes(profile_reader)

    client.get(BRIEFING, headers=headers)

    assert profile_reader.tokens == [headers["Authorization"].removeprefix("Bearer ")]


def test_get_returns_401_without_a_token(client: TestClient) -> None:
    use_fakes(FakeProfileReader(PROFILE))

    response = client.get(BRIEFING)

    assert response.status_code == 401
    assert ErrorResponse.model_validate(response.json()).error.code == "INVALID_TOKEN"


def test_get_returns_404_when_the_user_has_no_profile(
    client: TestClient, headers: dict[str, str]
) -> None:
    topic_catalog = FakeTopicCatalog(TOPICS)
    use_fakes(FakeProfileReader(None), topic_catalog)

    response = client.get(BRIEFING, headers=headers)

    assert response.status_code == 404
    assert ErrorResponse.model_validate(response.json()).error.code == "PROFILE_NOT_FOUND"
    # Without a profile there is nothing to build: Content Management is not called.
    assert topic_catalog.calls == 0


def test_get_passes_token_expired_through_from_personalization(
    client: TestClient, headers: dict[str, str]
) -> None:
    use_fakes(FakeProfileReader(PROFILE, error=TokenExpiredError()))

    response = client.get(BRIEFING, headers=headers)

    assert response.status_code == 401
    assert ErrorResponse.model_validate(response.json()).error.code == "TOKEN_EXPIRED"


@pytest.mark.parametrize(
    "unavailable",
    ["personalization", "topics", "articles"],
)
def test_get_returns_503_when_a_service_is_unavailable(
    client: TestClient, headers: dict[str, str], unavailable: str
) -> None:
    use_fakes(
        FakeProfileReader(PROFILE, available=unavailable != "personalization"),
        FakeTopicCatalog(TOPICS, available=unavailable != "topics"),
        FakeArticleCatalog([], available=unavailable != "articles"),
    )

    response = client.get(BRIEFING, headers=headers)

    assert response.status_code == 503
    assert (
        ErrorResponse.model_validate(response.json()).error.code == "SERVICE_UNAVAILABLE"
    )
