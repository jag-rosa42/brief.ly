from fastapi import APIRouter, status
from shared_errors import ErrorResponse

from src.api.dependencies import CurrentAccountIdDep, GetCurrentProfileDep
from src.api.schemas.profile import ProfileResponse

router = APIRouter(
    prefix="/me/profile",
    tags=["profile"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=ProfileResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def get_my_profile(
    account_id: CurrentAccountIdDep,
    get_current_profile: GetCurrentProfileDep,
) -> ProfileResponse:
    return ProfileResponse.from_domain(get_current_profile.execute(account_id))
