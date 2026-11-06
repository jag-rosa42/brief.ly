import pytest

from src.application.port.token.types import CreatedServiceToken
from src.application.use_cases.oauth.create_service_token import CreateServiceToken
from src.domain.exception import InvalidClientError, InvalidScopeError
from tests.fixtures.oauth import (
    CONTENT_MANAGEMENT,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    FakeClientSecretVerifier,
    FakeServiceTokenCreator,
)


class TestCreateServiceToken:
    def test_returns_a_token_for_an_allowed_request(
        self,
        create_service_token: CreateServiceToken,
        service_token_creator: FakeServiceTokenCreator,
    ) -> None:
        created: CreatedServiceToken = create_service_token.execute(
            client_id=TEST_CLIENT_ID,
            client_secret=TEST_CLIENT_SECRET,
            audience=CONTENT_MANAGEMENT,
            scopes=frozenset({"topics:read"}),
        )

        assert created.token == "fake-service-token-1"
        assert created.expires_in == 300
        assert service_token_creator.created == [
            (TEST_CLIENT_ID, CONTENT_MANAGEMENT, frozenset({"topics:read"}))
        ]

    def test_raises_invalid_client_for_a_wrong_secret(
        self,
        create_service_token: CreateServiceToken,
        service_token_creator: FakeServiceTokenCreator,
    ) -> None:
        with pytest.raises(InvalidClientError):
            create_service_token.execute(
                client_id=TEST_CLIENT_ID,
                client_secret="wrong-secret",
                audience=CONTENT_MANAGEMENT,
                scopes=frozenset({"topics:read"}),
            )
        assert service_token_creator.created == []

    def test_raises_invalid_client_for_an_unknown_client(
        self,
        create_service_token: CreateServiceToken,
        client_secret_verifier: FakeClientSecretVerifier,
    ) -> None:
        with pytest.raises(InvalidClientError):
            create_service_token.execute(
                client_id="unknown-client",
                client_secret=TEST_CLIENT_SECRET,
                audience=CONTENT_MANAGEMENT,
                scopes=frozenset({"topics:read"}),
            )
        # The secret is still checked, so an unknown client takes about as
        # long as a wrong secret.
        assert client_secret_verifier.calls == ["unknown-client"]

    def test_checks_the_client_before_the_scopes(
        self,
        create_service_token: CreateServiceToken,
    ) -> None:
        # A wrong secret with a forbidden scope: the caller learns nothing
        # about scopes.
        with pytest.raises(InvalidClientError):
            create_service_token.execute(
                client_id=TEST_CLIENT_ID,
                client_secret="wrong-secret",
                audience=CONTENT_MANAGEMENT,
                scopes=frozenset({"summaries:write"}),
            )

    def test_raises_invalid_scope_for_a_forbidden_scope(
        self,
        create_service_token: CreateServiceToken,
        service_token_creator: FakeServiceTokenCreator,
    ) -> None:
        with pytest.raises(InvalidScopeError):
            create_service_token.execute(
                client_id=TEST_CLIENT_ID,
                client_secret=TEST_CLIENT_SECRET,
                audience=CONTENT_MANAGEMENT,
                scopes=frozenset({"summaries:write"}),
            )
        assert service_token_creator.created == []

    def test_raises_invalid_scope_for_a_forbidden_audience(
        self,
        create_service_token: CreateServiceToken,
    ) -> None:
        with pytest.raises(InvalidScopeError):
            create_service_token.execute(
                client_id=TEST_CLIENT_ID,
                client_secret=TEST_CLIENT_SECRET,
                audience="transcendence:identity",
                scopes=frozenset({"topics:read"}),
            )

    def test_raises_invalid_scope_when_no_scope_is_requested(
        self,
        create_service_token: CreateServiceToken,
    ) -> None:
        with pytest.raises(InvalidScopeError):
            create_service_token.execute(
                client_id=TEST_CLIENT_ID,
                client_secret=TEST_CLIENT_SECRET,
                audience=CONTENT_MANAGEMENT,
                scopes=frozenset(),
            )
