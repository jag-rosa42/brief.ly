from fastapi import APIRouter, status
from shared_errors import ErrorResponse

from src.api.dependencies import ListTopicsDep, UpdateTopicSummaryDep
from src.api.dependencies.service_auth import SUMMARIES_WRITE, TOPICS_READ
from src.api.schemas.topic import TopicResponse, UpdateTopicSummaryRequest

router = APIRouter(
    prefix="/topics",
    tags=["topics"],
)


@router.get(
    path="",
    dependencies=[TOPICS_READ],
    status_code=status.HTTP_200_OK,
    response_model=list[TopicResponse],
)
def list_topics(list_topics: ListTopicsDep) -> list[TopicResponse]:
    return [TopicResponse.from_domain(topic) for topic in list_topics.execute()]


@router.put(
    path="/{topic_id}/summary",
    dependencies=[SUMMARIES_WRITE],
    status_code=status.HTTP_200_OK,
    response_model=TopicResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
def update_topic_summary(
    topic_id: str,
    body: UpdateTopicSummaryRequest,
    update_topic_summary: UpdateTopicSummaryDep,
) -> TopicResponse:
    topic = update_topic_summary.execute(
        topic_id=topic_id,
        text=body.text,
        llm_model=body.llm_model,
        generation_duration_ms=body.generation_duration_ms,
    )
    return TopicResponse.from_domain(topic)
