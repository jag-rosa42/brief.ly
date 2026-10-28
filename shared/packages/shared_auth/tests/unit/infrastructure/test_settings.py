import pytest
from pydantic import ValidationError

from shared_auth.infrastructure.settings import AuthSettings
from tests.fixtures.factory import (
    ACCESS_AUDIENCE,
    PUBLIC_API_AUDIENCE,
    SERVICE_AUDIENCE,
)


class TestAuthSettings:
    def test_issuer_and_access_audience_have_defaults(self, public_key_pem: str) -> None:
        settings = AuthSettings(
            _env_file=None,
            JWT_PUBLIC_KEY=public_key_pem,
            JWT_SERVICE_AUDIENCE=SERVICE_AUDIENCE,
        )

        # Whatever their values, a service doesn't have to set them.
        assert settings.JWT_ISSUER
        assert settings.JWT_ACCESS_AUDIENCE
        assert settings.JWT_PUBLIC_API_AUDIENCE is None

    def test_service_audience_is_required(self, public_key_pem: str) -> None:
        # No safe default: a service must say who it is.
        with pytest.raises(ValidationError):
            AuthSettings(_env_file=None, JWT_PUBLIC_KEY=public_key_pem)

    def test_public_key_is_required(self) -> None:
        with pytest.raises(ValidationError):
            AuthSettings(_env_file=None, JWT_SERVICE_AUDIENCE=SERVICE_AUDIENCE)


class TestAcceptedAudiences:
    def test_with_a_public_api(self, auth_settings: AuthSettings) -> None:
        assert auth_settings.accepted_audiences == {
            ACCESS_AUDIENCE,
            SERVICE_AUDIENCE,
            PUBLIC_API_AUDIENCE,
        }

    def test_without_a_public_api(
        self, auth_settings_without_public_api: AuthSettings
    ) -> None:
        assert auth_settings_without_public_api.accepted_audiences == {
            ACCESS_AUDIENCE,
            SERVICE_AUDIENCE,
        }
