from functools import lru_cache

from shared_auth import ClientCredentialsTokenProvider

from src.infrastructure.config.service_client import (
    CLIENT_ID,
    CONTENT_MANAGEMENT_AUDIENCE,
    CONTENT_MANAGEMENT_SCOPES,
    TOKEN_PATH,
    ServiceClientSettings,
)


@lru_cache  # one provider for the whole app, so its cached token is shared
def get_content_management_token_provider() -> ClientCredentialsTokenProvider:
    client_settings = ServiceClientSettings()
    return ClientCredentialsTokenProvider(
        issuer_service="identity",
        token_endpoint_url=f"{client_settings.IDENTITY_URL}{TOKEN_PATH}",
        client_id=CLIENT_ID,
        client_secret=client_settings.MORNING_BRIEFING_CLIENT_SECRET,
        audience=CONTENT_MANAGEMENT_AUDIENCE,
        scopes=CONTENT_MANAGEMENT_SCOPES,
    )
