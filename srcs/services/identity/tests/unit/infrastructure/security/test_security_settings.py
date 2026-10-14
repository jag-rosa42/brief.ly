"""
Tests for SecuritySettings (src/infrastructure/security/settings.py).

These tests verify that:
- the defaults match the token model
- the database settings do not require the JWT keys, so the migration
  container can run without them
- the cookie settings moved out to CookieSettings
"""

from src.infrastructure.database.config.settings import DatabaseSettings
from src.infrastructure.security.settings import SecuritySettings


def _default(field: str):
    return SecuritySettings.model_fields[field].default


def test_defaults_follow_the_token_model() -> None:
    assert _default("JWT_ISSUER") == "transcendence:identity"
    assert _default("JWT_ACCESS_AUDIENCE") == "transcendence:api"
    assert _default("JWT_REFRESH_AUDIENCE") == "transcendence:identity"
    assert _default("ACCESS_TOKEN_EXPIRE_MINUTES") == 15
    assert _default("REFRESH_TOKEN_EXPIRE_DAYS") == 7


def test_access_and_refresh_audiences_differ() -> None:
    assert _default("JWT_ACCESS_AUDIENCE") != _default("JWT_REFRESH_AUDIENCE")


def test_keys_are_required() -> None:
    assert SecuritySettings.model_fields["JWT_PRIVATE_KEY"].is_required()
    assert SecuritySettings.model_fields["JWT_PUBLIC_KEY"].is_required()


def test_database_settings_do_not_need_jwt_keys() -> None:
    """The migration container only loads the database settings."""
    jwt_fields: set[str] = {
        name for name in DatabaseSettings.model_fields if name.startswith("JWT_")
    }

    assert jwt_fields == set()


def test_cookie_settings_are_not_here_anymore() -> None:
    cookie_fields: set[str] = {
        name
        for name in SecuritySettings.model_fields
        if name.startswith("REFRESH_COOKIE")
    }

    assert cookie_fields == set()