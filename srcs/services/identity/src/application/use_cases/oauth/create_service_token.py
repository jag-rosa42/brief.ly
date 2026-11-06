from src.application.port.service_client.registry import ServiceClientRegistry
from src.application.port.service_client.secret_verifier import ClientSecretVerifier
from src.application.port.service_client.token_creator import ServiceTokenCreator
from src.application.port.token.types import CreatedServiceToken
from src.domain.entities.service_client import ServiceClient
from src.domain.exception import InvalidClientError, InvalidScopeError


class CreateServiceToken:
    def __init__(
        self,
        client_registry: ServiceClientRegistry,
        client_secret_verifier: ClientSecretVerifier,
        service_token_creator: ServiceTokenCreator,
    ) -> None:
        self._client_registry: ServiceClientRegistry = client_registry
        self._client_secret_verifier: ClientSecretVerifier = client_secret_verifier
        self._service_token_creator: ServiceTokenCreator = service_token_creator

    def execute(
        self,
        client_id: str,
        client_secret: str,
        audience: str,
        scopes: frozenset[str],
    ) -> CreatedServiceToken:
        secret_is_valid: bool = self._client_secret_verifier.verify(
            client_id,
            client_secret,
        )
        client: ServiceClient | None = self._client_registry.find(client_id)
        if client is None or not secret_is_valid:
            raise InvalidClientError()
        if not client.may_request(audience, scopes):
            raise InvalidScopeError()
        return self._service_token_creator.create_service_token(
            client_id=client.client_id,
            audience=audience,
            scopes=scopes,
        )
