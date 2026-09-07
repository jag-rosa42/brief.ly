import logging
from datetime import datetime

from src.application.ports import (
    ArticleDiscoverer,
    ArticleExtractor,
    NormalizedArticleRepository,
    SourceRepository,
)
from src.domain.entities import (
    DiscoveredArticle,
    Source,
)

logger = logging.getLogger(__name__)


class SynchronizeSources:
    """
    Fetch and normalize articles of list due from source repository,
    persist normalized article in article repository
    """

    def __init__(
        self,
        source_repository: SourceRepository,
        normalized_article_repository: NormalizedArticleRepository,
        article_discoverer: ArticleDiscoverer,
        article_extractor: ArticleExtractor,
    ):
        self.article_extractor = article_extractor
        self.article_discoverer = article_discoverer
        self.source_repository = source_repository
        self.normalized_article_repository = normalized_article_repository

    def execute(self, synchronized_at: datetime) -> None:
        sources = self.source_repository.list_due(synchronized_at)

        for source in sources:
            self._sync_source(source, synchronized_at)

    def _sync_source(self, source: Source, synchronized_at: datetime) -> None:
        try:
            discovered_articles = self.article_discoverer.discover(source)

            for discovered in discovered_articles:
                self._process_article(source, discovered)

            self.source_repository.update_last_successful_sync(
                source.id,
                synchronized_at,
            )
            self.source_repository.commit()

        except Exception:
            logger.exception(
                "source synchronization failed",
                extra={"source_id": source.id},
            )
            return

        logger.info(
            "source synchronization succeeded",
            extra={"source_id": source.id},
        )

    def _process_article(self, source: Source, discovered: DiscoveredArticle):
        if self.normalized_article_repository.exists(
            source.id,
            discovered.external_id,
        ):
            return

        try:
            normalized_article = self.article_extractor.extract(discovered)
            self.normalized_article_repository.save(
                    source.id, normalized_article
                    )

        except Exception:
            logger.exception(
                "article synchronization failed",
                extra={"discovered": discovered.external_id},
            )
