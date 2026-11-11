from fastapi import APIRouter, status
from shared_auth import PublicApiReaderDep
from shared_errors import ErrorResponse

from src.api.dependencies import ListTopicsDep
from src.api.schemas.topic import TopicsResponse

# Public twin of /topics (ADR-0009). The catalog belongs to no user, but the
# route still needs a key with "read", like every public route.
router = APIRouter(
    prefix="/topics",
    tags=["topics"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=TopicsResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def get_public_topics(
    list_topics: ListTopicsDep,
    user: PublicApiReaderDep,
) -> TopicsResponse:
    return TopicsResponse.from_domain(list_topics.execute())
