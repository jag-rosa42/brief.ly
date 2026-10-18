from src.api.schemas import TopicResponse
from src.domain.entities import Topic


def test_topic_response_maps_a_topic_identifier():
    response = TopicResponse.from_domain(Topic(id="science"))

    assert response.model_dump() == {"id": "science"}
    assert isinstance(response.id, str)
