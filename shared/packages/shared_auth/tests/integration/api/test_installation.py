"""
install_authentication: a bad configuration must stop the service at startup,
not answer 500 to its first request.
"""

import pytest
from fastapi import FastAPI

from shared_auth.api.installation import install_authentication
from shared_auth.infrastructure.settings import AuthSettings


class TestPublicApiFlag:
    def test_public_api_without_its_audience_fails_at_startup(
        self, auth_settings_without_public_api: AuthSettings
    ) -> None:
        with pytest.raises(ValueError, match="JWT_PUBLIC_API_AUDIENCE"):
            install_authentication(
                FastAPI(), auth_settings_without_public_api, public_api=True
            )

    def test_public_api_with_its_audience_installs(
        self, auth_settings: AuthSettings
    ) -> None:
        app = FastAPI()

        authenticator = install_authentication(app, auth_settings, public_api=True)

        assert app.state.authenticator is authenticator

    def test_no_public_api_needs_no_audience(
        self, auth_settings_without_public_api: AuthSettings
    ) -> None:
        # Most services have no public API: the flag's default must not
        # require the audience.
        app = FastAPI()

        authenticator = install_authentication(app, auth_settings_without_public_api)

        assert app.state.authenticator is authenticator
