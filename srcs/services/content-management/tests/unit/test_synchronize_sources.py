from unittest.mock import Mock

import pytest

from src.application.port import (
    ArticleDiscoverer,
    ArticleDiscoveryError,
    ArticleExtractor,
)
from src.application.use_cases.ingestion import SynchronizeSources
from src.domain.repositories import NormalizedArticleRepository, SourceRepository
from tests.fixtures.unit_of_work import FakeUnitOfWork


def build_synchronize_sources(
    uow: FakeUnitOfWork,
    source_repository: Mock,
    normalized_article_repository: Mock,
    article_discoverer: Mock,
    article_extractor: Mock,
) -> SynchronizeSources:
    return SynchronizeSources(
        uow=uow,
        source_repository=source_repository,
        normalized_article_repository=normalized_article_repository,
        article_discoverer=article_discoverer,
        article_extractor=article_extractor,
    )


@pytest.fixture
def dependencies():
    return {
        "source_repository": Mock(spec=SourceRepository),
        "normalized_article_repository": Mock(spec=NormalizedArticleRepository),
        "article_discoverer": Mock(spec=ArticleDiscoverer),
        "article_extractor": Mock(spec=ArticleExtractor),
    }


def test_commits_a_successful_synchronization(
    source,
    discovered_article,
    normalized_article,
    synchronization_time,
    uow,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source]
    dependencies["article_discoverer"].discover.return_value = [discovered_article]
    dependencies["normalized_article_repository"].exists.return_value = False
    dependencies["article_extractor"].extract.return_value = normalized_article

    build_synchronize_sources(uow, **dependencies).execute(synchronization_time)

    dependencies["normalized_article_repository"].save.assert_called_once_with(
        source.id, normalized_article
    )
    dependencies["source_repository"].update_last_successful_sync.assert_called_once_with(
        source.id, synchronization_time
    )
    assert uow.commit_count == 1


def test_isolates_an_expected_source_failure(
    source,
    source_b,
    discovered_article,
    synchronization_time,
    uow,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source, source_b]
    dependencies["article_discoverer"].discover.side_effect = [
        ArticleDiscoveryError("NewsAPI unavailable"),
        [discovered_article],
    ]
    dependencies["normalized_article_repository"].exists.return_value = True

    build_synchronize_sources(uow, **dependencies).execute(synchronization_time)

    dependencies["source_repository"].update_last_successful_sync.assert_called_once_with(
        source_b.id, synchronization_time
    )
    assert uow.commit_count == 1


def test_unexpected_discovery_error_rolls_back_and_propagates(
    source,
    synchronization_time,
    uow,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source]
    dependencies["article_discoverer"].discover.side_effect = RuntimeError(
        "programming error"
    )

    with pytest.raises(RuntimeError, match="programming error"):
        build_synchronize_sources(uow, **dependencies).execute(synchronization_time)

    assert uow.commit_count == 0
    assert uow.rollback_count == 1


def test_persistence_error_rolls_back_and_propagates(
    source,
    discovered_article,
    normalized_article,
    synchronization_time,
    uow,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source]
    dependencies["article_discoverer"].discover.return_value = [discovered_article]
    dependencies["normalized_article_repository"].exists.return_value = False
    dependencies["article_extractor"].extract.return_value = normalized_article
    dependencies["normalized_article_repository"].save.side_effect = RuntimeError(
        "database unavailable"
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        build_synchronize_sources(uow, **dependencies).execute(synchronization_time)

    assert uow.commit_count == 0
    assert uow.rollback_count == 1
