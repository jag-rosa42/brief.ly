from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep
from src.domain.repositories import (
    NormalizedArticleRepository,
    SourceRepository,
    TopicRepository,
)
from src.infrastructure.database.repositories import (
    SqlAlchemyNormalizedArticleRepository,
    SqlAlchemySourceRepository,
    SqlAlchemyTopicRepository,
)


def get_normalized_article_repository(
    session: SessionDep,
) -> NormalizedArticleRepository:
    return SqlAlchemyNormalizedArticleRepository(session)


NormalizedArticleRepositoryDep = Annotated[
    NormalizedArticleRepository,
    Depends(get_normalized_article_repository),
]


def get_source_repository(session: SessionDep) -> SourceRepository:
    return SqlAlchemySourceRepository(session)


SourceRepositoryDep = Annotated[
    SourceRepository,
    Depends(get_source_repository),
]


def get_topic_repository(session: SessionDep) -> TopicRepository:
    return SqlAlchemyTopicRepository(session)


TopicRepositoryDep = Annotated[
    TopicRepository,
    Depends(get_topic_repository),
]
