from fastapi import APIRouter, status

from src.api.dependencies import ListTopicsDep
from src.api.schemas.topic import TopicResponse

router = APIRouter(
    prefix="/topics",
    tags=["topics"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=list[TopicResponse],
)
def list_topics(list_topics: ListTopicsDep) -> list[TopicResponse]:
    return [TopicResponse.from_domain(topic) for topic in list_topics.execute()]
