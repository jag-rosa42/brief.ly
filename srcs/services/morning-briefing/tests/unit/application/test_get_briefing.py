from uuid import uuid4

import pytest

from src.application.exceptions import (
    ArticleCatalogUnavailableError,
    TopicCatalogUnavailableError,
)
from src.application.use_cases.get_briefing import GetBriefing
from src.domain.entities.briefing import TopicCluster
from src.domain.entities.profile import Profile
from src.domain.entities.topic import Topic
from src.domain.exception import ProfileNotFoundError
from tests.fakes import (
    FakeArticleCatalog,
    FakeProfileReader,
    FakeTopicCatalog,
    article,
)

TOKEN = "user-token"
PROFILE = Profile(
    name="John",
    topic_ids=("science", "business"),
    saved_article_ids=(uuid4(),),
)
SCIENCE = article("science", uuid4())
BUSINESS = article("business", uuid4())
SPORTS = article("sports", uuid4())


def test_execute_builds_one_cluster_per_interest_in_the_profile_order() -> None:
    use_case = GetBriefing(
        FakeProfileReader(PROFILE),
        FakeTopicCatalog(
            [
                Topic(id="business", summary="Markets are calm."),
                Topic(id="science", summary=None),
                Topic(id="sports", summary="A big final."),
            ]
        ),
        FakeArticleCatalog([SCIENCE, BUSINESS, SPORTS]),
    )

    briefing = use_case.execute(TOKEN)

    assert briefing.profile == PROFILE
    assert briefing.topic_clusters == (
        TopicCluster(topic_id="science", summary=None, articles=(SCIENCE,)),
        TopicCluster(
            topic_id="business", summary="Markets are calm.", articles=(BUSINESS,)
        ),
    )


def test_execute_forwards_the_user_token_to_the_profile_reader() -> None:
    profile_reader = FakeProfileReader(PROFILE)
    use_case = GetBriefing(profile_reader, FakeTopicCatalog([]), FakeArticleCatalog([]))

    use_case.execute(TOKEN)

    assert profile_reader.tokens == [TOKEN]


def test_execute_keeps_a_topic_unknown_to_the_catalog_without_summary() -> None:
    use_case = GetBriefing(
        FakeProfileReader(PROFILE), FakeTopicCatalog([]), FakeArticleCatalog([SCIENCE])
    )

    briefing = use_case.execute(TOKEN)

    assert briefing.topic_clusters[0] == TopicCluster(
        topic_id="science", summary=None, articles=(SCIENCE,)
    )
    assert briefing.topic_clusters[1].articles == ()


def test_execute_raises_without_a_profile_and_does_not_call_content_management() -> None:
    topic_catalog = FakeTopicCatalog([])
    article_catalog = FakeArticleCatalog([])
    use_case = GetBriefing(FakeProfileReader(None), topic_catalog, article_catalog)

    with pytest.raises(ProfileNotFoundError):
        use_case.execute(TOKEN)

    assert topic_catalog.calls == 0
    assert article_catalog.calls == []


def test_execute_raises_when_the_topic_catalog_is_unavailable() -> None:
    use_case = GetBriefing(
        FakeProfileReader(PROFILE),
        FakeTopicCatalog([], available=False),
        FakeArticleCatalog([]),
    )

    with pytest.raises(TopicCatalogUnavailableError):
        use_case.execute(TOKEN)


def test_execute_raises_when_the_article_catalog_is_unavailable() -> None:
    use_case = GetBriefing(
        FakeProfileReader(PROFILE),
        FakeTopicCatalog([]),
        FakeArticleCatalog([], available=False),
    )

    with pytest.raises(ArticleCatalogUnavailableError):
        use_case.execute(TOKEN)
