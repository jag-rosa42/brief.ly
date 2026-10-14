"""
Tests for CookieSettings (src/infrastructure/config/cookie.py).
"""

from src.infrastructure.config.cookie import CookieSettings


def _default(field: str):
    return CookieSettings.model_fields[field].default


def test_refresh_cookie_name() -> None:
    assert _default("REFRESH_COOKIE_NAME") == "refresh_token"


def test_refresh_cookie_is_scoped_to_the_auth_path_seen_by_the_browser() -> None:
    # The gateway strips "/api/identity", but the browser only sends the
    # cookie to URLs starting with this path.
    assert _default("REFRESH_COOKIE_PATH") == "/api/identity/auth"


def test_has_no_required_field() -> None:
    # Importing cookie.py must never fail because of a missing env variable.
    required: list[str] = [
        name for name, field in CookieSettings.model_fields.items() if field.is_required()
    ]

    assert required == []