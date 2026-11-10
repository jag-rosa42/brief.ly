from fastapi import APIRouter, Response, status
from shared_errors import ErrorResponse

from src.api.dependencies.api_key import OptionalApiKeyHeaderDep, VerifyApiKeyDep

router = APIRouter(
    prefix="/api-keys",
    tags=["api-keys"],
)

# Traefik's ForwardAuth calls this route with GET, whatever the method of the
# original request (unless its `preserveRequestMethod` option is set). The
# route still accepts every method, as the contract asks, so a change in the
# gateway configuration can't break the public API.
#
# Only GET is documented: one function documented under several methods gets
# the same OpenAPI operation ID for each, and FastAPI warns about duplicates.
# The other methods are served by the same function, on a hidden route.
OTHER_FORWARD_AUTH_METHODS: list[str] = ["HEAD", "POST", "PUT", "PATCH", "DELETE"]


@router.get(
    path="/verify",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    responses={
        status.HTTP_200_OK: {
            "description": "Empty body; the public API token is in the "
            "Authorization header",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ErrorResponse,
            "description": "INVALID_API_KEY (missing, unknown, revoked or expired)",
        },
    },
)
@router.api_route(
    path="/verify",
    methods=OTHER_FORWARD_AUTH_METHODS,
    response_class=Response,
    include_in_schema=False,
)
def verify_api_key(
    verify_api_key: VerifyApiKeyDep,
    api_key: OptionalApiKeyHeaderDep,
) -> Response:
    """Exchange the `X-API-Key` header for a public API token (ADR-0009).

    Called only by the gateway's ForwardAuth, never routed from outside.
    On 200, the gateway copies our Authorization header into the request it
    forwards to the service (`authResponseHeaders: [Authorization]`),
    replacing whatever the program sent. On any other status, the gateway
    returns our answer to the program as is.
    """
    token: str = verify_api_key.execute(api_key)
    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "Authorization": f"Bearer {token}",
            # The answer holds a token: nothing may cache it.
            "Cache-Control": "no-store",
        },
    )
