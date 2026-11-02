import pytest

from src.application.exceptions import TopicCatalogUnavailableError
from src.application.use_cases.list_topics import ListTopics
from src.domain.entities.topic import Topic
from tests.fakes import FakeTopicCatalog

CATALOG = ["science", "sports", "health", "business"]


def test_execute_returns_topics_sorted_by_id() -> None:
    catalog = FakeTopicCatalog(CATALOG)
    use_case = ListTopics(catalog)

    topics = use_case.execute()

    assert topics == [
        Topic(id="business"),
        Topic(id="health"),
        Topic(id="science"),
        Topic(id="sports"),
    ]


def test_execute_raises_when_catalog_is_unavailable() -> None:
    catalog = FakeTopicCatalog(CATALOG, available=False)
    use_case = ListTopics(catalog)

    with pytest.raises(TopicCatalogUnavailableError):
        use_case.execute()
