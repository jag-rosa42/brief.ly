from functools import lru_cache

from shared_auth import ClientCredentialsTokenProvider

from src.infrastructure.config.service_token import ServiceTokenSettings

# Contract: docs/api/06_service-to-service.md. The client ID, audience and
# scopes must match this service's entry in Identity's registry
# (identity/src/infrastructure/oauth/service_clients.py).
TOKEN_PATH = "/internal/v1/oauth/token"
CLIENT_ID = "morning-briefing"
CONTENT_MANAGEMENT_AUDIENCE = "transcendence:content-management"
# One token for both catalogs: they run in the same process, so one token per
# catalog would not protect anything more.
CONTENT_MANAGEMENT_SCOPES = ("topics:read", "articles:read")


@lru_cache  # one provider for the whole app, so its cached token is shared
def get_content_management_token_provider() -> ClientCredentialsTokenProvider:
    settings = ServiceTokenSettings()
    return ClientCredentialsTokenProvider(
        issuer_service="identity",
        token_endpoint_url=f"{settings.IDENTITY_URL}{TOKEN_PATH}",
        client_id=CLIENT_ID,
        client_secret=settings.MORNING_BRIEFING_CLIENT_SECRET,
        audience=CONTENT_MANAGEMENT_AUDIENCE,
        scopes=CONTENT_MANAGEMENT_SCOPES,
    )
