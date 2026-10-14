from src.infrastructure.config.base import ServiceSettings


class CookieSettings(ServiceSettings):
    """
    How the refresh token travels over HTTP (cookie name and browser path).

    The token's lifetime is a token concern and stays in SecuritySettings
    (REFRESH_TOKEN_EXPIRE_DAYS). Only the running service loads it; the
    migration container does not need any of these values.
    """

    REFRESH_COOKIE_NAME: str = "refresh_token"

    # The path as the BROWSER sees it. The gateway removes "/api/identity"
    # before forwarding, so Identity receives "/auth/refresh", but the browser
    # only sends a cookie when the URL it requests starts with this path.
    REFRESH_COOKIE_PATH: str = "/api/identity/auth"


cookie_settings = CookieSettings()
