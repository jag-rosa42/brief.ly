from fastapi import APIRouter, status
from shared_auth import PublicApiReaderDep
from shared_errors import ErrorResponse

from src.api.dependencies import GetBriefingDep
from src.api.schemas.briefing import BriefingResponse

# Public twin of /briefing (ADR-0009): same use case, same body. The path
# names the resource, not the service: /public/v1/morning-briefing.
router = APIRouter(
    prefix="/morning-briefing",
    tags=["briefing"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=BriefingResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def get_public_briefing(
    user: PublicApiReaderDep,
    get_briefing: GetBriefingDep,
) -> BriefingResponse:
    # The profile belongs to the key's owner: the public API token is
    # forwarded to Personalization, whose internal route accepts it
    # (CurrentForwardedUserDep). ADR-0008 and ADR-0009: a public route that
    # calls another service for the user forwards the user's token.
    return BriefingResponse.from_domain(get_briefing.execute(user.token))
