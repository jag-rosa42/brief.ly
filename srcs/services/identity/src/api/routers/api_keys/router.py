from uuid import UUID

from fastapi import APIRouter, Response, status
from shared_errors import ErrorResponse

from src.api.dependencies import CurrentAccountDep
from src.api.dependencies.api_key import (
    CreateApiKeyDep,
    ListApiKeysDep,
    RevokeApiKeyDep,
)
from src.api.schemas.api_key import (
    ApiKeyListResponse,
    CreateApiKeyRequest,
    CreatedApiKeyResponse,
)
from src.application.use_cases.api_keys.create_api_key import CreatedApiKey
from src.domain.entities.api_key import ApiKey

router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "INVALID_TOKEN or TOKEN_EXPIRED",
        },
    },
)


@router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    response_model=CreatedApiKeyResponse,
    responses={
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "API_KEY_LIMIT_REACHED (already 5 active keys)",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "VALIDATION_ERROR",
        },
    },
)
def create_api_key(
    body: CreateApiKeyRequest,
    current_account: CurrentAccountDep,
    create_api_key: CreateApiKeyDep,
    response: Response,
) -> CreatedApiKeyResponse:
    created: CreatedApiKey = create_api_key.execute(
        account_id=current_account.id,
        name=body.name,
        scopes=frozenset(body.scopes),
    )
    # The body holds a secret, shown once: no cache may keep a copy.
    response.headers["Cache-Control"] = "no-store"
    return CreatedApiKeyResponse.from_created(created)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=ApiKeyListResponse,
)
def list_api_keys(
    current_account: CurrentAccountDep,
    list_api_keys: ListApiKeysDep,
) -> ApiKeyListResponse:
    api_keys: list[ApiKey] = list_api_keys.execute(account_id=current_account.id)
    return ApiKeyListResponse.from_domain(api_keys)


@router.delete(
    path="/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "VALIDATION_ERROR (key_id not a UUID)",
        },
    },
)
def revoke_api_key(
    key_id: UUID,
    current_account: CurrentAccountDep,
    revoke_api_key: RevokeApiKeyDep,
) -> None:
    revoke_api_key.execute(account_id=current_account.id, api_key_id=key_id)
