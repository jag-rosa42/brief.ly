from fastapi import APIRouter, status
from shared_auth import CurrentUserDep
from shared_errors import ErrorResponse

from src.api.dependencies import ListTopicsDep
from src.api.schemas.topic import TopicsResponse

router = APIRouter(
    prefix="/topics",
    tags=["topics"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=TopicsResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def get_topics(
    list_topics: ListTopicsDep,
    user: CurrentUserDep,
) -> TopicsResponse:
    topics = list_topics.execute()
    return TopicsResponse.from_domain(topics)
