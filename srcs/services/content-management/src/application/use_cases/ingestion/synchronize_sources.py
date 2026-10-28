import logging
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.application.port import (
    ArticleDiscoverer,
    ArticleDiscoveryError,
    ArticleExtractionError,
    ArticleExtractor,
    IngestionLock,
    UnitOfWork,
)
from src.domain.entities import DiscoveredArticle, Source
from src.domain.exception import ArticleIngestionAlreadyRunningError
from src.domain.repositories import NormalizedArticleRepository, SourceRepository

logger = logging.getLogger(__name__)


class ArticleSynchronizationOutcome(StrEnum):
    CREATED = "created"
    UNCHANGED = "unchanged"
    FAILED = "failed"


@dataclass(frozen=True)
class SynchronizationResult:
    articles_created: int = 0
    failures: int = 0
    sources_succeeded: int = 0
    sources_failed: int = 0

    @property
    def has_failures(self) -> bool:
        return self.failures > 0

    @property
    def succeeded(self) -> bool:
        return not self.has_failures or self.sources_succeeded > 0


class SynchronizeSources:
    """Discover, normalize, and persist articles from every due source."""

    def __init__(
        self,
        uow: UnitOfWork,
        ingestion_lock: IngestionLock,
        source_repository: SourceRepository,
        normalized_article_repository: NormalizedArticleRepository,
        article_discoverer: ArticleDiscoverer,
        article_extractor: ArticleExtractor,
    ) -> None:
        self._uow = uow
        self._ingestion_lock = ingestion_lock
        self._source_repository = source_repository
        self._normalized_article_repository = normalized_article_repository
        self._article_discoverer = article_discoverer
        self._article_extractor = article_extractor

    def execute(self, synchronized_at: datetime) -> SynchronizationResult:
        total_articles_created = 0
        total_failures = 0
        total_sources_succeeded = 0
        total_sources_failed = 0

        if not self._ingestion_lock.try_acquire():
            raise ArticleIngestionAlreadyRunningError()

        try:
            with self._uow:
                sources: list[Source] = self._source_repository.list_due(synchronized_at)
                # End the source-list read transaction before source discovery.
                self._uow.commit()

                for source in sources:
                    source_result: SynchronizationResult = self._sync_source(
                        source,
                        synchronized_at,
                    )
                    # Persist each source independently so a later failure does not
                    # roll back sources that were already synchronized.
                    self._uow.commit()
                    total_articles_created += source_result.articles_created
                    total_failures += source_result.failures
                    total_sources_succeeded += source_result.sources_succeeded
                    total_sources_failed += source_result.sources_failed
        finally:
            self._ingestion_lock.release()

        return SynchronizationResult(
            articles_created=total_articles_created,
            failures=total_failures,
            sources_succeeded=total_sources_succeeded,
            sources_failed=total_sources_failed,
        )

    def _sync_source(
        self, source: Source, synchronized_at: datetime
    ) -> SynchronizationResult:
        try:
            discovered_articles = self._article_discoverer.discover(source)
        except ArticleDiscoveryError:
            logger.exception(
                "source synchronization failed",
                extra={"source_id": source.id},
            )
            return SynchronizationResult(failures=1, sources_failed=1)

        known_external_ids = (
            self._normalized_article_repository.find_existing_external_ids(
                source.id,
                [discovered.external_id for discovered in discovered_articles],
            )
        )
        articles_created = 0
        article_failures = 0

        for discovered in discovered_articles:
            outcome = self._process_article(
                source,
                discovered,
                known_external_ids,
            )
            articles_created += outcome is ArticleSynchronizationOutcome.CREATED
            article_failures += outcome is ArticleSynchronizationOutcome.FAILED

        source_log_context = {
            "source_id": source.id,
            "articles_succeeded": len(discovered_articles) - article_failures,
            "articles_total": len(discovered_articles),
            "articles_created": articles_created,
            "article_failures": article_failures,
        }

        if article_failures > 0 and articles_created == 0:
            logger.warning(
                "source synchronization failed",
                extra=source_log_context,
            )
            return SynchronizationResult(
                failures=article_failures,
                sources_failed=1,
            )

        self._source_repository.update_last_successful_sync(
            source.id,
            synchronized_at,
        )

        logger.info(
            "source synchronization completed",
            extra=source_log_context,
        )
        return SynchronizationResult(
            articles_created=articles_created,
            failures=article_failures,
            sources_succeeded=1,
        )

    def _process_article(
        self,
        source: Source,
        discovered: DiscoveredArticle,
        known_external_ids: set[str],
    ) -> ArticleSynchronizationOutcome:
        if discovered.external_id in known_external_ids:
            return ArticleSynchronizationOutcome.UNCHANGED

        try:
            normalized_article = self._article_extractor.extract(discovered)
        except ArticleExtractionError:
            logger.exception(
                "article synchronization failed",
                extra={"discovered_external_id": discovered.external_id},
            )
            return ArticleSynchronizationOutcome.FAILED

        self._normalized_article_repository.save(source.id, normalized_article)
        known_external_ids.add(discovered.external_id)
        return ArticleSynchronizationOutcome.CREATED
