import logging
from datetime import datetime

from src.application.port import (
    ArticleDiscoverer,
    ArticleDiscoveryError,
    ArticleExtractionError,
    ArticleExtractor,
    UnitOfWork,
)
from src.domain.entities import DiscoveredArticle, Source
from src.domain.repositories import NormalizedArticleRepository, SourceRepository

logger = logging.getLogger(__name__)


class SynchronizeSources:
    """Discover, normalize, and persist articles from every due source."""

    def __init__(
        self,
        uow: UnitOfWork,
        source_repository: SourceRepository,
        normalized_article_repository: NormalizedArticleRepository,
        article_discoverer: ArticleDiscoverer,
        article_extractor: ArticleExtractor,
    ) -> None:
        self._uow = uow
        self._source_repository = source_repository
        self._normalized_article_repository = normalized_article_repository
        self._article_discoverer = article_discoverer
        self._article_extractor = article_extractor

    def execute(self, synchronized_at: datetime) -> None:
        with self._uow:
            sources = self._source_repository.list_due(synchronized_at)

            for source in sources:
                self._sync_source(source, synchronized_at)

            self._uow.commit()

    def _sync_source(self, source: Source, synchronized_at: datetime) -> None:
        try:
            discovered_articles = self._article_discoverer.discover(source)
        except ArticleDiscoveryError:
            logger.exception(
                "source synchronization failed",
                extra={"source_id": source.id},
            )
            return

        for discovered in discovered_articles:
            self._process_article(source, discovered)

        self._source_repository.update_last_successful_sync(
            source.id,
            synchronized_at,
        )

        logger.info(
            "source synchronization completed",
            extra={"source_id": source.id},
        )

    def _process_article(
        self, source: Source, discovered: DiscoveredArticle
    ) -> None:
        if self._normalized_article_repository.exists(
            source.id,
            discovered.external_id,
        ):
            return

        try:
            normalized_article = self._article_extractor.extract(discovered)
        except ArticleExtractionError:
            logger.exception(
                "article synchronization failed",
                extra={"discovered": discovered.external_id},
            )
            return

        self._normalized_article_repository.save(source.id, normalized_article)
