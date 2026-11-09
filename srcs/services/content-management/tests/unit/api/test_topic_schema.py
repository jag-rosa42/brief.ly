from datetime import UTC, datetime

from src.api.schemas import TopicResponse
from src.domain.entities import Topic, TopicSummary


def test_topic_response_maps_a_topic_without_summary():
    response = TopicResponse.from_domain(Topic(id="science"))

    assert response.model_dump() == {
        "id": "science",
        "summary": None,
        "summarized_at": None,
    }
    assert isinstance(response.id, str)


def test_topic_response_maps_summary_without_exposing_llm_model():
    summarized_at = datetime(2026, 11, 3, 9, 30, tzinfo=UTC)
    topic = Topic(
        id="science",
        summary=TopicSummary(
            text="Science summary",
            summarized_at=summarized_at,
            llm_model="private-model",
        ),
    )

    response = TopicResponse.from_domain(topic)

    assert response.model_dump() == {
        "id": "science",
        "summary": "Science summary",
        "summarized_at": summarized_at,
    }
