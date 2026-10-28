import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from src.application.port import (
    ArticleDiscoverer,
    ArticleDiscoveryError,
    ArticleExtractionError,
    ArticleExtractor,
    IngestionLock,
    UnitOfWork,
)
from src.domain.entities import DiscoveredArticle, Source
from src.domain.exception import IngestionAlreadyRunningError
from src.domain.repositories import NormalizedArticleRepository, SourceRepository

logger = logging.getLogger(__name__)

ArticleSynchronizationOutcome = Literal["created", "unchanged", "failed"]


@dataclass(frozen=True)
class SynchronizationResult:
    articles_created: int = 0
    failures: int = 0

    @property
    def has_failures(self) -> bool:
        return self.failures > 0

    @property
    def succeeded(self) -> bool:
        return not self.has_failures or self.articles_created > 0


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
        with self._uow:
            if not self._ingestion_lock.try_acquire():
                raise IngestionAlreadyRunningError()

            sources = self._source_repository.list_due(synchronized_at)
            result = SynchronizationResult()

            for source in sources:
                source_result = self._sync_source(source, synchronized_at)
                result = SynchronizationResult(
                    articles_created=(
                        result.articles_created + source_result.articles_created
                    ),
                    failures=result.failures + source_result.failures,
                )

            self._uow.commit()

        return result

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
            return SynchronizationResult(failures=1)

        articles_created = 0
        article_failures = 0

        for discovered in discovered_articles:
            outcome = self._process_article(source, discovered)
            articles_created += outcome == "created"
            article_failures += outcome == "failed"

        if article_failures > 0 and articles_created == 0:
            return SynchronizationResult(failures=article_failures)

        self._source_repository.update_last_successful_sync(
            source.id,
            synchronized_at,
        )

        logger.info(
            "source synchronization completed",
            extra={
                "source_id": source.id,
                "articles_created": articles_created,
                "article_failures": article_failures,
            },
        )
        return SynchronizationResult(
            articles_created=articles_created,
            failures=article_failures,
        )

    def _process_article(
        self, source: Source, discovered: DiscoveredArticle
    ) -> ArticleSynchronizationOutcome:
        if self._normalized_article_repository.exists(
            source.id,
            discovered.external_id,
        ):
            return "unchanged"

        try:
            normalized_article = self._article_extractor.extract(discovered)
        except ArticleExtractionError:
            logger.exception(
                "article synchronization failed",
                extra={"discovered_external_id": discovered.external_id},
            )
            return "failed"

        self._normalized_article_repository.save(source.id, normalized_article)
        return "created"
