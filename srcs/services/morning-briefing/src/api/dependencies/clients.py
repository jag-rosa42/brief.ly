from functools import lru_cache

from shared_auth import DownstreamClient

from src.api.dependencies.service_token import get_content_management_token_provider
from src.infrastructure.clients.content_management import CONTENT_MANAGEMENT_SERVICE
from src.infrastructure.config.app import app_settings

# One DownstreamClient per downstream service, built on first use and shared
# by every client of that service: it keeps one connection pool.


@lru_cache
def get_content_management_client() -> DownstreamClient:
    return DownstreamClient(
        CONTENT_MANAGEMENT_SERVICE, app_settings.CONTENT_MANAGEMENT_URL
    )


@lru_cache
def get_personalization_client() -> DownstreamClient:
    # The profile belongs to the user: the reader forwards their token.
    return DownstreamClient("personalization", app_settings.PERSONALIZATION_URL)


def close_clients() -> None:
    """Close the HTTP clients and the token provider, when the app stops.

    Only the ones that were created: calling a getter here would build one
    (and, for the token provider, read the client secret) just to close it.
    """
    for getter in (
        get_content_management_client,
        get_content_management_token_provider,
        get_personalization_client,
    ):
        if getter.cache_info().currsize:
            getter().close()
