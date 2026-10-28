"""
Authenticator: the right kind of token for each kind of caller.

The verifier already accepted every token here (valid signature, accepted
audience): these tests only check the type/audience pairing and the subject.
"""

import pytest

from shared_auth.api.installation import build_authenticator
from shared_auth.application.authenticator import Authenticator
from shared_auth.domain.exceptions import InvalidTokenError
from shared_auth.domain.principals import ServicePrincipal, UserPrincipal
from shared_auth.infrastructure.settings import AuthSettings
from tests.fixtures.factory import (
    ACCESS_AUDIENCE,
    ACCOUNT_ID,
    PUBLIC_API_AUDIENCE,
    READ_SCOPE,
    SERVICE_AUDIENCE,
    SERVICE_NAME,
    WRITE_SCOPE,
)
from tests.fixtures.security import TokenFactory


class TestUser:
    def test_browser_access_token(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        token: str = make_token()

        user: UserPrincipal = authenticator.user(token)

        assert user.account_id == ACCOUNT_ID
        assert user.scopes == frozenset()
        assert user.token == token  # kept unchanged, for forwarding

    def test_refuses_a_public_api_token(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        token: str = make_token(overrides={"aud": PUBLIC_API_AUDIENCE})

        with pytest.raises(InvalidTokenError):
            authenticator.user(token)

    def test_refuses_a_service_token(
        self, authenticator: Authenticator, service_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            authenticator.user(service_token(READ_SCOPE))

    def test_refuses_an_access_token_addressed_to_the_service_audience(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        # Right type for a user, but an audience reserved for service tokens.
        token: str = make_token(overrides={"aud": SERVICE_AUDIENCE})

        with pytest.raises(InvalidTokenError):
            authenticator.user(token)

    def test_refuses_a_subject_that_is_not_an_account_id(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            authenticator.user(make_token(overrides={"sub": "not-a-uuid"}))


class TestPublicApiUser:
    def test_public_api_token(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        token: str = make_token(
            overrides={"aud": PUBLIC_API_AUDIENCE, "scope": READ_SCOPE}
        )

        user: UserPrincipal = authenticator.public_api_user(token)

        assert user.account_id == ACCOUNT_ID
        assert user.scopes == {READ_SCOPE}

    def test_refuses_a_browser_token(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            authenticator.public_api_user(make_token())

    def test_fails_loudly_when_the_service_has_no_public_api(
        self,
        auth_settings_without_public_api: AuthSettings,
        make_token: TokenFactory,
    ) -> None:
        # A public route in a service without JWT_PUBLIC_API_AUDIENCE is a
        # setup bug, not a bad token: a 500 naming the setting, not a 401.
        authenticator = build_authenticator(auth_settings_without_public_api)
        token: str = make_token(overrides={"aud": PUBLIC_API_AUDIENCE})

        with pytest.raises(RuntimeError, match="JWT_PUBLIC_API_AUDIENCE"):
            authenticator.public_api_user(token)


class TestForwardedUser:
    """Internal routes: the calling service forwards the user's token."""

    def test_accepts_a_browser_access_token(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        token: str = make_token()

        user: UserPrincipal = authenticator.forwarded_user(token)

        assert user.account_id == ACCOUNT_ID
        assert user.token == token

    def test_accepts_a_public_api_token(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        # A public route of another service forwarding the public API token.
        token: str = make_token(
            overrides={"aud": PUBLIC_API_AUDIENCE, "scope": READ_SCOPE}
        )

        user: UserPrincipal = authenticator.forwarded_user(token)

        assert user.scopes == {READ_SCOPE}

    def test_refuses_a_service_token(
        self, authenticator: Authenticator, service_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            authenticator.forwarded_user(service_token(WRITE_SCOPE))

    def test_refuses_an_access_token_addressed_to_the_service_audience(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        token: str = make_token(overrides={"aud": SERVICE_AUDIENCE})

        with pytest.raises(InvalidTokenError):
            authenticator.forwarded_user(token)

    def test_refuses_a_public_api_token_when_the_service_has_no_public_api(
        self,
        auth_settings_without_public_api: AuthSettings,
        make_token: TokenFactory,
    ) -> None:
        authenticator = build_authenticator(auth_settings_without_public_api)
        token: str = make_token(overrides={"aud": PUBLIC_API_AUDIENCE})

        with pytest.raises(InvalidTokenError):
            authenticator.forwarded_user(token)


class TestService:
    def test_service_token(
        self, authenticator: Authenticator, service_token: TokenFactory
    ) -> None:
        token: str = service_token(READ_SCOPE)

        service: ServicePrincipal = authenticator.service(token)

        assert service.name == SERVICE_NAME
        assert service.scopes == {READ_SCOPE}
        assert service.token == token

    def test_refuses_a_user_token(
        self, authenticator: Authenticator, make_token: TokenFactory
    ) -> None:
        with pytest.raises(InvalidTokenError):
            authenticator.service(make_token())

    def test_refuses_a_service_token_for_the_user_audience(
        self, authenticator: Authenticator, service_token: TokenFactory
    ) -> None:
        token: str = service_token(overrides={"aud": ACCESS_AUDIENCE})

        with pytest.raises(InvalidTokenError):
            authenticator.service(token)

    @pytest.mark.parametrize("subject", [SERVICE_NAME, "service:", "user:123"])
    def test_refuses_a_malformed_service_subject(
        self, authenticator: Authenticator, service_token: TokenFactory, subject: str
    ) -> None:
        # The subject must be "service:<name>", with a non-empty name.
        with pytest.raises(InvalidTokenError):
            authenticator.service(service_token(overrides={"sub": subject}))
