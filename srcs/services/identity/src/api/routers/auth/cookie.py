from fastapi import Response

from src.infrastructure.config.cookie import cookie_settings
from src.infrastructure.security.settings import security_settings

SECONDS_PER_DAY: int = 24 * 60 * 60

# ----- Refresh token cookie attributes -----
#
# HttpOnly          JavaScript cannot read it, so an XSS cannot steal it.
# Secure            Only sent over HTTPS (browsers treat http://localhost as
#                   secure too, which helps in development).
# SameSite=Strict   Never sent on requests started by another website.
# Path              Only sent to the auth endpoints, not to every API call.
# Max-Age           Same lifetime as the refresh token itself.

# More details:
# - https://starlette.dev/responses/#set-cookie
# - https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies#security


def set_refresh_token_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=cookie_settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=security_settings.REFRESH_TOKEN_EXPIRE_DAYS * SECONDS_PER_DAY,
        path=cookie_settings.REFRESH_COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )


def clear_refresh_token_cookie(response: Response) -> None:
    response.delete_cookie(
        key=cookie_settings.REFRESH_COOKIE_NAME,
        path=cookie_settings.REFRESH_COOKIE_PATH,
        secure=True,
        httponly=True,
        samesite="strict",
    )
