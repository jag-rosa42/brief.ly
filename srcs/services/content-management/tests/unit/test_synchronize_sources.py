import logging
from unittest.mock import Mock

from src.application.port import ArticleDiscoverer, ArticleExtractor
from src.application.use_cases.ingestion import SynchronizeSources
from src.domain.repositories import NormalizedArticleRepository, SourceRepository


# Synchronization and save new normalized_article
def test_synchronize_sources_and_save_normalized_article(
    source, discovered_article, normalized_article, synchronization_time
):

    # ---------- ARRANGE --------------------
    # Define the mock for dependencies
    article_extractor = Mock(spec=ArticleExtractor)
    article_discoverer = Mock(spec=ArticleDiscoverer)
    source_repository = Mock(spec=SourceRepository)
    normalized_article_repository = Mock(spec=NormalizedArticleRepository)

    #  Define the return values of mocks
    article_extractor.extract.return_value = normalized_article
    article_discoverer.discover.return_value = [discovered_article]
    source_repository.list_due.return_value = [source]
    normalized_article_repository.exists.return_value = False

    # ---------- ACT ------------------------
    # Execute use case with dependencies
    SynchronizeSources(
        source_repository,
        normalized_article_repository,
        article_discoverer,
        article_extractor,
    ).execute(synchronization_time)

    # ---------- ASSERT ---------------------
    # make sure each mock dependencies are called once with coherent args
    source_repository.list_due.assert_called_once_with(synchronization_time)
    article_discoverer.discover.assert_called_once_with(source)
    normalized_article_repository.exists.assert_called_once_with(
        source.id, discovered_article.external_id
    )
    article_extractor.extract.assert_called_once_with(discovered_article)
    normalized_article_repository.save.assert_called_once_with(
        source.id, normalized_article
    )
    source_repository.update_last_successful_sync.assert_called_once_with(
        source.id, synchronization_time
    )


# Article already existing ignored
def test_ignore_already_existing_normalized_article(
    source,
    discovered_article,
    normalized_article,
    synchronization_time,
):

    # ---------- ARRANGE --------------------
    article_extractor = Mock(spec=ArticleExtractor)
    article_discoverer = Mock(spec=ArticleDiscoverer)
    source_repository = Mock(spec=SourceRepository)
    normalized_article_repository = Mock(spec=NormalizedArticleRepository)

    article_extractor.extract.return_value = normalized_article
    article_discoverer.discover.return_value = [discovered_article]
    source_repository.list_due.return_value = [source]
    normalized_article_repository.exists.return_value = True

    # ---------- ACT ------------------------
    SynchronizeSources(
        source_repository,
        normalized_article_repository,
        article_discoverer,
        article_extractor,
    ).execute(synchronization_time)

    # ---------- ASSERT ---------------------
    source_repository.list_due.assert_called_once_with(synchronization_time)
    article_discoverer.discover.assert_called_once_with(source)
    normalized_article_repository.exists.assert_called_once_with(
        source.id, discovered_article.external_id
    )
    article_extractor.extract.assert_not_called()
    normalized_article_repository.save.assert_not_called()
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
    article_extractor = Mock(spec=ArticleExtractor)
    article_discoverer = Mock(spec=ArticleDiscoverer)
    source_repository = Mock(spec=SourceRepository)
    normalized_article_repository = Mock(spec=NormalizedArticleRepository)

    article_discoverer.discover.return_value = []
    source_repository.list_due.return_value = [source]
    normalized_article_repository.exists.return_value = True

    # ---------- ACT ------------------------
    SynchronizeSources(
        source_repository,
        normalized_article_repository,
        article_discoverer,
        article_extractor,
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
    discovered_article,
    normalized_article,
    synchronization_time,
):

    # ---------- ARRANGE --------------------
    article_extractor = Mock(spec=ArticleExtractor)
    article_discoverer = Mock(spec=ArticleDiscoverer)
    source_repository = Mock(spec=SourceRepository)
    normalized_article_repository = Mock(spec=NormalizedArticleRepository)

    article_extractor.extract.return_value = normalized_article
    article_discoverer.discover.side_effect = [
        RuntimeError("NewsAPI indisponible"),
        [discovered_article],
    ]
    source_repository.list_due.return_value = [source, source_b]
    normalized_article_repository.exists.return_value = True

    # ---------- ACT ------------------------
    with caplog.at_level(
        logging.ERROR,
        logger="src.application.use_cases.ingestion.synchronize_sources",
    ):
        SynchronizeSources(
            source_repository,
            normalized_article_repository,
            article_discoverer,
            article_extractor,
        ).execute(synchronization_time)

    # ---------- ASSERT ---------------------
    source_repository.list_due.assert_called_once_with(synchronization_time)
    normalized_article_repository.exists.assert_called_once_with(
        source_b.id, discovered_article.external_id
    )
    article_extractor.extract.assert_not_called()
    normalized_article_repository.save.assert_not_called()
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
