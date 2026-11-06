from typing import Annotated

from fastapi import APIRouter, Form, Response, status
from shared_errors import ErrorResponse

from src.api.dependencies.oauth import ClientCredentialsDep, CreateServiceTokenDep
from src.api.errors.exceptions import UnsupportedGrantTypeError
from src.api.schemas.oauth import ServiceTokenResponse
from src.application.port.token.types import CreatedServiceToken

CLIENT_CREDENTIALS_GRANT: str = "client_credentials"

router = APIRouter(
    prefix="/oauth",
    tags=["oauth"],
)


@router.post(
    path="/token",
    status_code=status.HTTP_200_OK,
    response_model=ServiceTokenResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    },
)
def create_token(
    credentials: ClientCredentialsDep,
    create_service_token: CreateServiceTokenDep,
    response: Response,
    # RFC 6749 §4.4.2: the parameters are a form, not JSON.
    grant_type: Annotated[str, Form()],
    audience: Annotated[str, Form()],
    # Optional here so that a missing scope gets INVALID_SCOPE (from the use
    # case), like any scope the client may not have, not a generic 422.
    scope: Annotated[str, Form()] = "",
) -> ServiceTokenResponse:
    if grant_type != CLIENT_CREDENTIALS_GRANT:
        raise UnsupportedGrantTypeError()

    service_token: CreatedServiceToken = create_service_token.execute(
        client_id=credentials.client_id,
        client_secret=credentials.client_secret,
        audience=audience,
        # RFC 6749 §3.3: scopes are one space-separated string.
        scopes=frozenset(scope.split()),
    )

    # RFC 6749 §5.1: a response holding a token must never be cached.
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return ServiceTokenResponse.from_service_token(service_token)
