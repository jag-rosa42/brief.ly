import logging
from unittest.mock import Mock

from src.application.ports import (
        ArticleDiscoverer,
        ArticleExtractor,
        ArticleRepository,
        SourceRepository,
        )
from src.application.synchronize_sources import SynchronizeSources


# Synchronization and save new article
def test_synchronize_sources_and_save_article(
        source,
        discovered,
        extracted,
        synchronization_time
        ):

    # ---------- ARRANGE --------------------
    # Define the mock for dependencies
    extractor = Mock(spec=ArticleExtractor)
    discoverer = Mock(spec=ArticleDiscoverer)
    source_repository = Mock(spec=SourceRepository)
    article_repository = Mock(spec=ArticleRepository)

    #  Define the return values of mocks
    extractor.extract.return_value = extracted
    discoverer.discover.return_value = [discovered]
    source_repository.list_due.return_value = [source]
    article_repository.exists.return_value = False

    # ---------- ACT ------------------------
    # Execute use case with dependencies
    SynchronizeSources(
            source_repository,
            article_repository,
            discoverer,
            extractor,
            ).execute(synchronization_time)

    # ---------- ASSERT ---------------------
    # make sure each mock dependencies are called once with coherent args
    source_repository.list_due.assert_called_once_with(synchronization_time)
    discoverer.discover.assert_called_once_with(source)
    article_repository.exists.assert_called_once_with(
            source.id,
            discovered.external_id
            )
    extractor.extract.assert_called_once_with(discovered)
    article_repository.save.assert_called_once_with(source.id, extracted)
    source_repository.update_last_successful_sync.assert_called_once_with(
            source.id,
            synchronization_time
            )


# Article already existing ignored
def test_ignore_already_existing_article(
        source,
        discovered,
        extracted,
        synchronization_time,
        ):

    # ---------- ARRANGE --------------------
    extractor = Mock(spec=ArticleExtractor)
    discoverer = Mock(spec=ArticleDiscoverer)
    source_repository = Mock(spec=SourceRepository)
    article_repository = Mock(spec=ArticleRepository)

    extractor.extract.return_value = extracted
    discoverer.discover.return_value = [discovered]
    source_repository.list_due.return_value = [source]
    article_repository.exists.return_value = True

    # ---------- ACT ------------------------
    SynchronizeSources(
            source_repository,
            article_repository,
            discoverer,
            extractor,
            ).execute(synchronization_time)

    # ---------- ASSERT ---------------------
    source_repository.list_due.assert_called_once_with(synchronization_time)
    discoverer.discover.assert_called_once_with(source)
    article_repository.exists.assert_called_once_with(
            source.id,
            discovered.external_id
            )
    extractor.extract.assert_not_called()
    article_repository.save.assert_not_called()
    source_repository.update_last_successful_sync.assert_called_once_with(
            source.id,
            synchronization_time,
            )


# Update of last success
def test_update_of_last_success(
        source,
        synchronization_time,
        ):

    # ---------- ARRANGE --------------------
    extractor = Mock(spec=ArticleExtractor)
    discoverer = Mock(spec=ArticleDiscoverer)
    source_repository = Mock(spec=SourceRepository)
    article_repository = Mock(spec=ArticleRepository)

    discoverer.discover.return_value = []
    source_repository.list_due.return_value = [source]
    article_repository.exists.return_value = True

    # ---------- ACT ------------------------
    SynchronizeSources(
            source_repository,
            article_repository,
            discoverer,
            extractor,
            ).execute(synchronization_time)

    # ---------- ASSERT ---------------------
    source_repository.update_last_successful_sync.assert_called_once_with(
            source.id,
            synchronization_time,
            )


# Error isolated from other sources
def test_error_isolated_from_other_sources(
        caplog,
        source,
        source_b,
        discovered,
        extracted,
        synchronization_time,
        ):

    # ---------- ARRANGE --------------------
    extractor = Mock(spec=ArticleExtractor)
    discoverer = Mock(spec=ArticleDiscoverer)
    source_repository = Mock(spec=SourceRepository)
    article_repository = Mock(spec=ArticleRepository)

    extractor.extract.return_value = extracted
    discoverer.discover.side_effect = [
            RuntimeError('NewsAPI indisponible'),
            [discovered],
            ]
    source_repository.list_due.return_value = [source, source_b]
    article_repository.exists.return_value = True

    # ---------- ACT ------------------------
    with caplog.at_level(
            logging.ERROR,
            logger="src.application.synchronize_sources",
            ):
        SynchronizeSources(
                source_repository,
                article_repository,
                discoverer,
                extractor,
                ).execute(synchronization_time)

    # ---------- ASSERT ---------------------
    source_repository.list_due.assert_called_once_with(synchronization_time)
    article_repository.exists.assert_called_once_with(
            source_b.id,
            discovered.external_id
            )
    extractor.extract.assert_not_called()
    article_repository.save.assert_not_called()
    source_repository.update_last_successful_sync.assert_called_once_with(
            source_b.id,
            synchronization_time,
            )

    [error_record] = [
        record for record in caplog.records if record.levelno == logging.ERROR
    ]
    assert error_record.message == "source synchronization failed"
    assert error_record.source_id == source.id
    assert error_record.exc_info is not None

# Logs and retry
