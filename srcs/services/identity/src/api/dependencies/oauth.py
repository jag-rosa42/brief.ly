import base64
import binascii
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security.utils import get_authorization_scheme_param

from src.api.schemas.oauth import ClientCredentials
from src.application.port.service_client.registry import ServiceClientRegistry
from src.application.port.service_client.secret_verifier import ClientSecretVerifier
from src.application.port.service_client.token_creator import ServiceTokenCreator
from src.application.use_cases.oauth.create_service_token import CreateServiceToken
from src.domain.exception import InvalidClientError
from src.infrastructure.config.base import CLIENT_SECRETS_DIR
from src.infrastructure.oauth.client_secret_verifier import SecretFileClientSecretVerifier
from src.infrastructure.oauth.service_clients import InMemoryServiceClientRegistry
from src.infrastructure.security.token.token_service import JWTTokenService

# ---------------------------------------------------------------------------
# Client credentials (HTTP Basic)
# ---------------------------------------------------------------------------
# The client sends its ID and secret as `Authorization: Basic base64(id:secret)`
# (RFC 6749 §2.3.1, RFC 7617). That is what shared_auth's
# ClientCredentialsTokenProvider sends.
#
# Parsed here rather than with FastAPI's HTTPBasic: HTTPBasic answers a
# malformed header with its own {"detail": ...} error, even with
# auto_error=False, which bypasses our error format. Here, anything wrong
# becomes INVALID_CLIENT.


AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]


def get_client_credentials(
    authorization_header_value: AuthorizationHeader = None,
) -> ClientCredentials:
    if authorization_header_value is None:
        raise InvalidClientError()
    authentication_scheme, encoded_credential = get_authorization_scheme_param(
        authorization_header_value
    )
    if authentication_scheme.lower() != "basic" or not encoded_credential:
        raise InvalidClientError()

    try:
        decoded_credentials: str = base64.b64decode(
            encoded_credential,
            validate=True,
        ).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise InvalidClientError() from exc

    client_id, separator, client_secret = decoded_credentials.partition(":")
    if not separator or not client_id or not client_secret:
        raise InvalidClientError()
    return ClientCredentials(client_id=client_id, client_secret=client_secret)


ClientCredentialsDep = Annotated[ClientCredentials, Depends(get_client_credentials)]


# ---------------------------------------------------------------------------
# Service Client Registry
# ---------------------------------------------------------------------------
@lru_cache  # the registry never changes while the service runs: build it once
def get_service_client_registry() -> ServiceClientRegistry:
    return InMemoryServiceClientRegistry()


ServiceClientRegistryDep = Annotated[
    ServiceClientRegistry,
    Depends(get_service_client_registry),
]


# ---------------------------------------------------------------------------
# Client Secret Verifier
# ---------------------------------------------------------------------------
def get_client_secret_verifier() -> ClientSecretVerifier:
    return SecretFileClientSecretVerifier(
        secrets_dir=CLIENT_SECRETS_DIR,
        known_client_ids=get_service_client_registry().client_ids(),
    )


ClientSecretVerifierDep = Annotated[
    ClientSecretVerifier, Depends(get_client_secret_verifier)
]


# ---------------------------------------------------------------------------
# Service Token Creator
# ---------------------------------------------------------------------------
def get_service_token_creator() -> ServiceTokenCreator:
    return JWTTokenService()


ServiceTokenCreatorDep = Annotated[
    ServiceTokenCreator, Depends(get_service_token_creator)
]


# ---------------------------------------------------------------------------
# Create Service Token
# ---------------------------------------------------------------------------
def get_create_service_token(
    client_registry: ServiceClientRegistryDep,
    client_secret_verifier: ClientSecretVerifierDep,
    service_token_creator: ServiceTokenCreatorDep,
) -> CreateServiceToken:
    return CreateServiceToken(
        client_registry,
        client_secret_verifier,
        service_token_creator,
    )


CreateServiceTokenDep = Annotated[CreateServiceToken, Depends(get_create_service_token)]
