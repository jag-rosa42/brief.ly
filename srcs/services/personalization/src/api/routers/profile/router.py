from fastapi import APIRouter, Response, status
from shared_auth import CurrentUserDep
from shared_errors import ErrorResponse

from src.api.dependencies import (
    GetCurrentProfileDep,
    UpsertCurrentProfileDep,
)
from src.api.schemas.profile import ProfileResponse, UpsertProfileRequest

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
    user: CurrentUserDep,
    get_current_profile: GetCurrentProfileDep,
) -> ProfileResponse:
    return ProfileResponse.from_domain(get_current_profile.execute(user.account_id))


@router.put(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=ProfileResponse,
    responses={
        status.HTTP_201_CREATED: {
            "model": ProfileResponse,
            "description": "Profile created",
        },
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def upsert_my_profile(
    body: UpsertProfileRequest,
    response: Response,
    user: CurrentUserDep,
    upsert_current_profile: UpsertCurrentProfileDep,
) -> ProfileResponse:
    profile, created = upsert_current_profile.execute(
        user.account_id, name=body.name, topic_ids=body.topic_ids
    )
    if created:
        response.status_code = status.HTTP_201_CREATED
    return ProfileResponse.from_domain(profile)
