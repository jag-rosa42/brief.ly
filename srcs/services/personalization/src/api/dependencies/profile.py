from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep, UnitOfWorkDep
from src.api.dependencies.saved_article import SavedArticleRepositoryDep
from src.api.dependencies.topic_catalog import TopicCatalogDep
from src.application.use_cases.get_current_profile import GetCurrentProfile
from src.application.use_cases.get_internal_profile import GetInternalProfile
from src.application.use_cases.upsert_current_profile import UpsertCurrentProfile
from src.domain.repositories.profile_repository import ProfileRepository
from src.infrastructure.database.repositories.sqlalchemy_profile_repository import (
    SqlAlchemyProfileRepository,
)


def get_profile_repository(session: SessionDep) -> ProfileRepository:
    return SqlAlchemyProfileRepository(session)


ProfileRepositoryDep = Annotated[ProfileRepository, Depends(get_profile_repository)]


def get_current_profile(profile_repository: ProfileRepositoryDep) -> GetCurrentProfile:
    return GetCurrentProfile(profile_repository)


GetCurrentProfileDep = Annotated[GetCurrentProfile, Depends(get_current_profile)]


def get_internal_profile(
    profile_repository: ProfileRepositoryDep,
    saved_article_repository: SavedArticleRepositoryDep,
) -> GetInternalProfile:
    return GetInternalProfile(profile_repository, saved_article_repository)


GetInternalProfileDep = Annotated[GetInternalProfile, Depends(get_internal_profile)]


def get_upsert_current_profile(
    uow: UnitOfWorkDep,
    profile_repository: ProfileRepositoryDep,
    topic_catalog: TopicCatalogDep,
) -> UpsertCurrentProfile:
    return UpsertCurrentProfile(uow, profile_repository, topic_catalog)


UpsertCurrentProfileDep = Annotated[
    UpsertCurrentProfile, Depends(get_upsert_current_profile)
]
