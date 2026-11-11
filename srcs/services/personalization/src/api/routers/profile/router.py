from fastapi import APIRouter, Response, status
from shared_auth import CurrentUserDep
from shared_errors import ErrorResponse

from src.api.dependencies import (
    FindCurrentProfileDep,
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
    # null when the user hasn't created their profile yet (right after
    # sign-up): a normal state for the app, which then shows the profile
    # form. A 404 would make Chrome log an error in the console.
    response_model=ProfileResponse | None,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    },
)
def get_my_profile(
    user: CurrentUserDep,
    find_current_profile: FindCurrentProfileDep,
) -> ProfileResponse | None:
    profile = find_current_profile.execute(user.account_id)
    return None if profile is None else ProfileResponse.from_domain(profile)


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
