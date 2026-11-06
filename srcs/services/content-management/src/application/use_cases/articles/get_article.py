from uuid import UUID

from src.domain.entities import NormalizedArticle
from src.domain.exception import ArticleNotFoundError
from src.domain.repositories import NormalizedArticleRepository


class GetArticle:
    def __init__(self, repository: NormalizedArticleRepository) -> None:
        self._repository = repository

    def execute(self, article_id: UUID) -> NormalizedArticle:
        article = self._repository.get_by_id(article_id)
        if article is None or (article.summary is not None and article.summary.rejected):
            raise ArticleNotFoundError()
        return article
