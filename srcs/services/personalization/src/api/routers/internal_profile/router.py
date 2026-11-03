from fastapi import APIRouter, status
from shared_auth import CurrentForwardedUserDep
from shared_errors import ErrorResponse

from src.api.dependencies import (
    GetInternalProfileDep,
)
from src.api.schemas.profile import InternalProfileResponse

router = APIRouter(
    prefix="/me/profile",
    tags=["internal"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=InternalProfileResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
    },
)
def get_my_internal_profile(
    user: CurrentForwardedUserDep,
    get_internal_profile: GetInternalProfileDep,
) -> InternalProfileResponse:
    return InternalProfileResponse.from_domain(
        get_internal_profile.execute(user.account_id)
    )
