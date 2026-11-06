"""Checks on the real registry: they fail if a client gets too much power."""

from src.infrastructure.oauth.service_clients import (
    CONTENT_MANAGEMENT_AUDIENCE,
    SERVICE_CLIENTS,
    InMemoryServiceClientRegistry,
)


class TestServiceClients:
    def test_client_ids_are_unique(self) -> None:
        client_ids: list[str] = [client.client_id for client in SERVICE_CLIENTS]

        assert len(client_ids) == len(set(client_ids))

    def test_only_ai_processing_may_write_summaries(self) -> None:
        # ADR-0010: AI Processing is the only writer of summaries.
        writers: set[str] = {
            client.client_id
            for client in SERVICE_CLIENTS
            if "summaries:write"
            in client.allowed_scopes.get(CONTENT_MANAGEMENT_AUDIENCE, frozenset())
        }

        assert writers == {"ai-processing"}

    def test_every_audience_is_a_transcendence_service(self) -> None:
        for client in SERVICE_CLIENTS:
            for audience in client.allowed_scopes:
                assert audience.startswith("transcendence:")

    def test_no_client_may_get_a_token_for_identity_or_the_browser_api(self) -> None:
        # Service tokens are for internal routes; transcendence:api is the
        # audience of user access tokens (ADR-0007).
        for client in SERVICE_CLIENTS:
            assert "transcendence:identity" not in client.allowed_scopes
            assert "transcendence:api" not in client.allowed_scopes


class TestInMemoryServiceClientRegistry:
    def test_finds_a_registered_client(self) -> None:
        registry = InMemoryServiceClientRegistry()

        client = registry.find("personalization")

        assert client is not None
        assert client.client_id == "personalization"

    def test_returns_none_for_an_unknown_client(self) -> None:
        assert InMemoryServiceClientRegistry().find("unknown") is None

    def test_lists_its_client_ids(self) -> None:
        assert InMemoryServiceClientRegistry().client_ids() == {
            "personalization",
            "morning-briefing",
            "ai-processing",
        }
