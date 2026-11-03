from typing import Annotated

from fastapi import Depends

from src.api.dependencies.repositories import (
    NormalizedArticleRepositoryDep,
    TopicRepositoryDep,
)
from src.application.use_cases.articles import GetArticle, ListArticles


def get_list_articles(
    article_repository: NormalizedArticleRepositoryDep,
    topic_repository: TopicRepositoryDep,
) -> ListArticles:
    return ListArticles(article_repository, topic_repository)


ListArticlesDep = Annotated[ListArticles, Depends(get_list_articles)]


def get_article_use_case(repository: NormalizedArticleRepositoryDep) -> GetArticle:
    return GetArticle(repository)


GetArticleDep = Annotated[
    GetArticle,
    Depends(get_article_use_case),
]
