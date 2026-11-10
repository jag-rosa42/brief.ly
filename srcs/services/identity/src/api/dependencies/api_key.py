from typing import Annotated

from fastapi import Depends

from src.api.dependencies.account import AccountRepositoryDep
from src.api.dependencies.database import SessionDep, UnitOfWorkDep
from src.api.dependencies.security import TokenHasherDep
from src.application.port.api_key.generator import ApiKeyGenerator
from src.application.use_cases.api_keys.create_api_key import CreateApiKey
from src.application.use_cases.api_keys.list_api_keys import ListApiKeys
from src.application.use_cases.api_keys.revoke_api_key import RevokeApiKey
from src.domain.repositories.api_key_repository import ApiKeyRepository
from src.infrastructure.database.repositories.sqlalchemy_api_key_repository import (
    SqlAlchemyApiKeyRepository,
)
from src.infrastructure.security.api_key_generator import SecretsApiKeyGenerator


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
