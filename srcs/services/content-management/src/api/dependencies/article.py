from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import UnitOfWorkDep
from src.api.dependencies.repositories import (
    NormalizedArticleRepositoryDep,
    TopicRepositoryDep,
)
from src.application.use_cases.articles import (
    GetArticle,
    ListArticles,
    UpdateArticleSummary,
)


def get_list_articles(
    article_repository: NormalizedArticleRepositoryDep,
    topic_repository: TopicRepositoryDep,
) -> ListArticles:
    return ListArticles(article_repository, topic_repository)


ListArticlesDep = Annotated[ListArticles, Depends(get_list_articles)]


def get_article(article_repository: NormalizedArticleRepositoryDep) -> GetArticle:
    return GetArticle(article_repository)


GetArticleDep = Annotated[
    GetArticle,
    Depends(get_article),
]


def get_update_article_summary(
    uow: UnitOfWorkDep,
    article_repository: NormalizedArticleRepositoryDep,
) -> UpdateArticleSummary:
    return UpdateArticleSummary(uow=uow, repository=article_repository)


UpdateArticleSummaryDep = Annotated[
    UpdateArticleSummary,
    Depends(get_update_article_summary),
]
