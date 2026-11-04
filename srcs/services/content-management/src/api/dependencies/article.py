from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep
from src.api.dependencies.topic import TopicRepositoryDep
from src.application.use_cases.articles import ListArticles
from src.domain.repositories import NormalizedArticleRepository
from src.infrastructure.database.repositories import (
    SqlAlchemyNormalizedArticleRepository,
)


def get_normalized_article_repository(
    session: SessionDep,
) -> NormalizedArticleRepository:
    return SqlAlchemyNormalizedArticleRepository(session)


NormalizedArticleRepositoryDep = Annotated[
    NormalizedArticleRepository,
    Depends(get_normalized_article_repository),
]


def get_list_articles(
    article_repository: NormalizedArticleRepositoryDep,
    topic_repository: TopicRepositoryDep,
) -> ListArticles:
    return ListArticles(article_repository, topic_repository)


ListArticlesDep = Annotated[ListArticles, Depends(get_list_articles)]
