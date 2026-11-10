from typing import Annotated

from fastapi import Depends, Header

from src.api.dependencies.account import AccountRepositoryDep
from src.api.dependencies.database import SessionDep, UnitOfWorkDep
from src.api.dependencies.security import TokenHasherDep
from src.application.port.api_key.generator import ApiKeyGenerator
from src.application.port.api_key.token_creator import PublicApiTokenCreator
from src.application.use_cases.api_keys.create_api_key import CreateApiKey
from src.application.use_cases.api_keys.list_api_keys import ListApiKeys
from src.application.use_cases.api_keys.revoke_api_key import RevokeApiKey
from src.application.use_cases.api_keys.verify_api_key import VerifyApiKey
from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.infrastructure.database.repositories.sqlalchemy_api_key_repository import (
    SqlAlchemyApiKeyRepository,
)
from src.infrastructure.security.api_key_generator import SecretsApiKeyGenerator
from src.infrastructure.security.token.token_service import JWTTokenService


# ---------------------------------------------------------------------------
# API Key Repository
# ---------------------------------------------------------------------------
def get_api_key_repository(session: SessionDep) -> ApiKeyRepository:
    return SqlAlchemyApiKeyRepository(session)


ApiKeyRepositoryDep = Annotated[ApiKeyRepository, Depends(get_api_key_repository)]


# ---------------------------------------------------------------------------
# API Key Generator
# ---------------------------------------------------------------------------
def get_api_key_generator() -> ApiKeyGenerator:
    return SecretsApiKeyGenerator()


ApiKeyGeneratorDep = Annotated[ApiKeyGenerator, Depends(get_api_key_generator)]


# ---------------------------------------------------------------------------
# Create API Key
# ---------------------------------------------------------------------------
def get_create_api_key(
    uow: UnitOfWorkDep,
    account_repository: AccountRepositoryDep,
    api_key_repository: ApiKeyRepositoryDep,
    api_key_generator: ApiKeyGeneratorDep,
    token_hasher: TokenHasherDep,
) -> CreateApiKey:
    return CreateApiKey(
        uow,
        account_repository,
        api_key_repository,
        api_key_generator,
        token_hasher,
    )


CreateApiKeyDep = Annotated[CreateApiKey, Depends(get_create_api_key)]


# ---------------------------------------------------------------------------
# List API Keys
# ---------------------------------------------------------------------------
def get_list_api_keys(api_key_repository: ApiKeyRepositoryDep) -> ListApiKeys:
    return ListApiKeys(api_key_repository)


ListApiKeysDep = Annotated[ListApiKeys, Depends(get_list_api_keys)]


# ---------------------------------------------------------------------------
# Revoke API Key
# ---------------------------------------------------------------------------
def get_revoke_api_key(
    uow: UnitOfWorkDep,
    api_key_repository: ApiKeyRepositoryDep,
) -> RevokeApiKey:
    return RevokeApiKey(uow, api_key_repository)


RevokeApiKeyDep = Annotated[RevokeApiKey, Depends(get_revoke_api_key)]


# ---------------------------------------------------------------------------
# API Key header
# ---------------------------------------------------------------------------
# The header a third-party program sends on /public/v1 routes. Traefik's
# ForwardAuth copies the original request's headers into its call to the
# verify route, so Identity reads it here.
API_KEY_HEADER_NAME: str = "X-API-Key"

ApiKeyHeader = Annotated[str | None, Header(alias=API_KEY_HEADER_NAME)]


# FastAPI forbids a default inside Annotated[..., Header()], so this wrapper
# holds the "= None" once (like OptionalRefreshTokenCookieDep). A missing key
# reaches the use case, which answers INVALID_API_KEY, instead of a 422.
def get_api_key_if_present(api_key: ApiKeyHeader = None) -> str | None:
    return api_key


OptionalApiKeyHeaderDep = Annotated[str | None, Depends(get_api_key_if_present)]


# ---------------------------------------------------------------------------
# Public API Token Creator
# ---------------------------------------------------------------------------
def get_public_api_token_creator() -> PublicApiTokenCreator:
    return JWTTokenService()


PublicApiTokenCreatorDep = Annotated[
    PublicApiTokenCreator, Depends(get_public_api_token_creator)
]


# ---------------------------------------------------------------------------
# Verify API Key
# ---------------------------------------------------------------------------
def get_verify_api_key(
    api_key_repository: ApiKeyRepositoryDep,
    token_hasher: TokenHasherDep,
    public_api_token_creator: PublicApiTokenCreatorDep,
) -> VerifyApiKey:
    return VerifyApiKey(api_key_repository, token_hasher, public_api_token_creator)


VerifyApiKeyDep = Annotated[VerifyApiKey, Depends(get_verify_api_key)]
