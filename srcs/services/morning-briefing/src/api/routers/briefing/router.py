from fastapi import APIRouter, status
from shared_auth import CurrentUserDep
from shared_errors import ErrorResponse

from src.api.dependencies import GetBriefingDep
from src.api.schemas.briefing import BriefingResponse

router = APIRouter(
    prefix="/briefing",
    tags=["briefing"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=BriefingResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def get_briefing(
    user: CurrentUserDep,
    get_briefing: GetBriefingDep,
) -> BriefingResponse:
    # The profile belongs to the user: their token is forwarded to
    # Personalization (ADR-0008).
    return BriefingResponse.from_domain(get_briefing.execute(user.token))
