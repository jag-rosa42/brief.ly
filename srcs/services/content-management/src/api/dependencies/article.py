from typing import Annotated

from fastapi import Depends

from src.api.dependencies.repositories import (
    NormalizedArticleRepositoryDep,
    TopicRepositoryDep,
)
from src.application.use_cases.articles import ListArticles


def get_list_articles(
    article_repository: NormalizedArticleRepositoryDep,
    topic_repository: TopicRepositoryDep,
) -> ListArticles:
    return ListArticles(article_repository, topic_repository)


ListArticlesDep = Annotated[ListArticles, Depends(get_list_articles)]
