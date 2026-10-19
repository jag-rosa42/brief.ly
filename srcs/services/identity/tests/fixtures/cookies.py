"""
Refresh token cookie helpers for API tests.

The refresh cookie is scoped to the path the BROWSER uses
(/api/identity/auth), while tests call the service directly (/auth/...).
It is also marked Secure, and the TestClient talks plain HTTP.

So the TestClient's cookie jar would never send the cookie back on its own.
Tests therefore:
- read the cookie and its attributes from the Set-Cookie header, and
- send it back explicitly in a Cookie header, with the CSRF header.

This is what the browser actually sends through the gateway.
"""

from http.cookies import Morsel, SimpleCookie

import pytest
from httpx2 import Response

from src.api.dependencies.security import (
    ANTI_CSRF_HEADER_NAME,
    ANTI_CSRF_HEADER_VALUE,
)
from src.infrastructure.config.cookie import cookie_settings

REFRESH_COOKIE_NAME: str = cookie_settings.REFRESH_COOKIE_NAME
REFRESH_COOKIE_PATH: str = cookie_settings.REFRESH_COOKIE_PATH


def get_refresh_cookie(response: Response) -> Morsel:
    """Return the refresh cookie set by the response (fails if absent)."""
    cookie: SimpleCookie = SimpleCookie()
    for header in response.headers.get_list("set-cookie"):
        cookie.load(header)

    if REFRESH_COOKIE_NAME not in cookie:
        pytest.fail(f"the response did not set the {REFRESH_COOKIE_NAME!r} cookie")
    return cookie[REFRESH_COOKIE_NAME]


def cookie_session_headers(
    refresh_token: str | None = None,
    *,
    csrf: bool = True,
) -> dict[str, str]:
    """Headers the frontend sends to /auth/refresh and /auth/logout."""
    headers: dict[str, str] = {}
    if csrf:
        headers[ANTI_CSRF_HEADER_NAME] = ANTI_CSRF_HEADER_VALUE
    if refresh_token is not None:
        headers["Cookie"] = f"{REFRESH_COOKIE_NAME}={refresh_token}"
    return headers
