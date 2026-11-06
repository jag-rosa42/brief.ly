from src.domain.entities.service_client import ServiceClient

CONTENT_MANAGEMENT: str = "transcendence:content-management"


def build_client() -> ServiceClient:
    return ServiceClient(
        client_id="personalization",
        allowed_scopes={CONTENT_MANAGEMENT: frozenset({"topics:read", "articles:read"})},
    )


class TestServiceClientMayRequest:
    def test_accepts_one_allowed_scope(self) -> None:
        assert build_client().may_request(CONTENT_MANAGEMENT, frozenset({"topics:read"}))

    def test_accepts_every_allowed_scope_at_once(self) -> None:
        assert build_client().may_request(
            CONTENT_MANAGEMENT, frozenset({"topics:read", "articles:read"})
        )

    def test_refuses_a_scope_it_may_not_have(self) -> None:
        assert not build_client().may_request(
            CONTENT_MANAGEMENT, frozenset({"topics:read", "summaries:write"})
        )

    def test_refuses_an_audience_it_may_not_call(self) -> None:
        assert not build_client().may_request(
            "transcendence:identity", frozenset({"topics:read"})
        )

    def test_refuses_an_empty_scope_request(self) -> None:
        assert not build_client().may_request(CONTENT_MANAGEMENT, frozenset())
