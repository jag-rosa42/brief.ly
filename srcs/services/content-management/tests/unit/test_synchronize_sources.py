import logging
from unittest.mock import Mock

import pytest

from src.application.port import (
    ArticleDiscoverer,
    ArticleDiscoveryError,
    ArticleExtractionError,
    ArticleExtractor,
)
from src.application.use_cases.ingestion import SynchronizationResult, SynchronizeSources
from src.domain.exception import IngestionAlreadyRunningError
from src.domain.repositories import NormalizedArticleRepository, SourceRepository
from tests.fixtures.ingestion_lock import FakeIngestionLock
from tests.fixtures.unit_of_work import FakeUnitOfWork


def build_synchronize_sources(
    uow: FakeUnitOfWork,
    ingestion_lock: FakeIngestionLock,
    source_repository: Mock,
    normalized_article_repository: Mock,
    article_discoverer: Mock,
    article_extractor: Mock,
) -> SynchronizeSources:
    return SynchronizeSources(
        uow=uow,
        ingestion_lock=ingestion_lock,
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


def test_synchronizes_and_saves_a_new_article(
    source,
    discovered_article,
    normalized_article,
    synchronization_time,
    uow,
    ingestion_lock,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source]
    dependencies["article_discoverer"].discover.return_value = [discovered_article]
    dependencies["normalized_article_repository"].exists.return_value = False
    dependencies["article_extractor"].extract.return_value = normalized_article

    result = build_synchronize_sources(uow, ingestion_lock, **dependencies).execute(
        synchronization_time
    )

    dependencies["normalized_article_repository"].save.assert_called_once_with(
        source.id, normalized_article
    )
    dependencies["source_repository"].update_last_successful_sync.assert_called_once_with(
        source.id, synchronization_time
    )
    assert result == SynchronizationResult(articles_created=1)
    assert uow.commit_count == 1
    assert ingestion_lock.acquire_count == 1


def test_ignores_an_existing_article(
    source,
    discovered_article,
    synchronization_time,
    uow,
    ingestion_lock,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source]
    dependencies["article_discoverer"].discover.return_value = [discovered_article]
    dependencies["normalized_article_repository"].exists.return_value = True

    result = build_synchronize_sources(uow, ingestion_lock, **dependencies).execute(
        synchronization_time
    )

    dependencies["article_extractor"].extract.assert_not_called()
    dependencies["normalized_article_repository"].save.assert_not_called()
    dependencies["source_repository"].update_last_successful_sync.assert_called_once_with(
        source.id, synchronization_time
    )
    assert result == SynchronizationResult()
    assert uow.commit_count == 1


def test_isolates_an_expected_source_failure(
    caplog,
    source,
    source_b,
    discovered_article,
    synchronization_time,
    uow,
    ingestion_lock,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source, source_b]
    dependencies["article_discoverer"].discover.side_effect = [
        ArticleDiscoveryError("NewsAPI unavailable"),
        [discovered_article],
    ]
    dependencies["normalized_article_repository"].exists.return_value = True

    with caplog.at_level(
        logging.ERROR,
        logger="src.application.use_cases.ingestion.synchronize_sources",
    ):
        result = build_synchronize_sources(uow, ingestion_lock, **dependencies).execute(
            synchronization_time
        )

    dependencies["source_repository"].update_last_successful_sync.assert_called_once_with(
        source_b.id, synchronization_time
    )
    assert result == SynchronizationResult(failures=1)
    assert not result.succeeded
    assert uow.commit_count == 1


def test_commits_a_partial_source_when_an_article_was_created(
    source,
    discovered_article,
    normalized_article,
    synchronization_time,
    uow,
    ingestion_lock,
    dependencies,
) -> None:
    failed_article = Mock(external_id="failed-article")
    dependencies["source_repository"].list_due.return_value = [source]
    dependencies["article_discoverer"].discover.return_value = [
        discovered_article,
        failed_article,
    ]
    dependencies["normalized_article_repository"].exists.return_value = False
    dependencies["article_extractor"].extract.side_effect = [
        normalized_article,
        ArticleExtractionError("article unavailable"),
    ]

    result = build_synchronize_sources(uow, ingestion_lock, **dependencies).execute(
        synchronization_time
    )

    assert result == SynchronizationResult(articles_created=1, failures=1)
    assert result.succeeded
    assert result.has_failures
    dependencies["source_repository"].update_last_successful_sync.assert_called_once_with(
        source.id, synchronization_time
    )
    assert uow.commit_count == 1


def test_failed_articles_without_creation_leave_the_source_due(
    source,
    discovered_article,
    synchronization_time,
    uow,
    ingestion_lock,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source]
    dependencies["article_discoverer"].discover.return_value = [discovered_article]
    dependencies["normalized_article_repository"].exists.return_value = False
    dependencies["article_extractor"].extract.side_effect = ArticleExtractionError(
        "article unavailable"
    )

    result = build_synchronize_sources(uow, ingestion_lock, **dependencies).execute(
        synchronization_time
    )

    assert result == SynchronizationResult(failures=1)
    dependencies["source_repository"].update_last_successful_sync.assert_not_called()
    assert uow.commit_count == 1


def test_rejects_a_second_ingestion_before_querying_sources(
    synchronization_time,
    uow,
    dependencies,
) -> None:
    ingestion_lock = FakeIngestionLock(acquired=False)

    with pytest.raises(IngestionAlreadyRunningError):
        build_synchronize_sources(uow, ingestion_lock, **dependencies).execute(
            synchronization_time
        )

    dependencies["source_repository"].list_due.assert_not_called()
    assert uow.commit_count == 0
    assert uow.rollback_count == 1


def test_unexpected_discovery_error_rolls_back_and_propagates(
    source,
    synchronization_time,
    uow,
    ingestion_lock,
    dependencies,
) -> None:
    dependencies["source_repository"].list_due.return_value = [source]
    dependencies["article_discoverer"].discover.side_effect = RuntimeError(
        "programming error"
    )

    with pytest.raises(RuntimeError, match="programming error"):
        build_synchronize_sources(uow, ingestion_lock, **dependencies).execute(
            synchronization_time
        )

    assert uow.commit_count == 0
    assert uow.rollback_count == 1


def test_persistence_error_rolls_back_and_propagates(
    source,
    discovered_article,
    normalized_article,
    synchronization_time,
    uow,
    ingestion_lock,
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
        build_synchronize_sources(uow, ingestion_lock, **dependencies).execute(
            synchronization_time
        )

    assert uow.commit_count == 0
    assert uow.rollback_count == 1
