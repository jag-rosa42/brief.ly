from typing import Annotated

from fastapi import Depends

from src.api.dependencies.database import SessionDep
from src.application.use_cases.get_current_profile import GetCurrentProfile
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
