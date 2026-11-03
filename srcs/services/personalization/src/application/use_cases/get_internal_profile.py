from dataclasses import dataclass
from uuid import UUID

from src.domain.entities.profile import Profile
from src.domain.exception import ProfileNotFoundError
from src.domain.repositories.profile_repository import ProfileRepository
from src.domain.repositories.saved_article_repository import SavedArticleRepository


@dataclass(frozen=True)
class InternalProfile:
    profile: Profile
    saved_article_ids: list[UUID]


class GetInternalProfile:
    def __init__(
        self,
        profile_repository: ProfileRepository,
        saved_article_repository: SavedArticleRepository,
    ) -> None:
        self._profiles: ProfileRepository = profile_repository
        self._saved_articles: SavedArticleRepository = saved_article_repository

    def execute(self, account_id: UUID) -> InternalProfile:
        profile: Profile | None = self._profiles.find_by_id(account_id)
        if profile is None:
            raise ProfileNotFoundError()
        saved_articles = self._saved_articles.list_for_account(account_id)
        saved_article_ids: list[UUID] = [
            saved_article.article_id for saved_article in saved_articles
        ]
        return InternalProfile(profile=profile, saved_article_ids=saved_article_ids)
