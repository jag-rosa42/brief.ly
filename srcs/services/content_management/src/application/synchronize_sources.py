import logging
from datetime import datetime

from src.application.ports import (
    ArticleDiscoverer,
    ArticleExtractor,
    ArticleRepository,
    SourceRepository,
)

logger = logging.getLogger(__name__)


class SynchronizeSources:
    def __init__(
            self,
            source_repository: SourceRepository,
            article_repository: ArticleRepository,
            discoverer: ArticleDiscoverer,
            extractor: ArticleExtractor,
            ):
        self.extractor = extractor
        self.discoverer = discoverer
        self.source_repository = source_repository
        self.article_repository = article_repository

    def execute(self, synchronized_at: datetime) -> None:
        sources = self.source_repository.list_due(synchronized_at)

        for source in sources:
            try:

                discovered_articles = self.discoverer.discover(source)

                for discovered in discovered_articles:
                    if self.article_repository.exists(
                            source.id,
                            discovered.external_id,
                            ):
                        continue

                    try:
                        extracted = self.extractor.extract(discovered)
                        self.article_repository.save(source.id, extracted)
                    except Exception:
                        logger.exception(
                            "article synchronization failed",
                            extra={
                                "discovered": discovered.external_id,
                                },
                        )
                        continue

                self.source_repository.update_last_successful_sync(
                        source.id,
                        synchronized_at,
                    )
            except Exception:
                logger.exception(
                    "source synchronization failed",
                    extra={
                        "source_id": source.id,
                    },
                )
                continue

            logger.info(
                "source synchronization succeeded",
                extra={"source_id": source.id},
            )
