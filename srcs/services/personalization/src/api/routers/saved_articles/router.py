from uuid import UUID

from fastapi import APIRouter, status
from shared_auth import CurrentUserDep
from shared_errors import ErrorResponse

from src.api.dependencies import (
    DeleteSavedArticleDep,
    ListSavedArticlesDep,
    SaveArticleDep,
)
from src.api.schemas.saved_article import SavedArticleResponse, SavedArticlesResponse

router = APIRouter(
    prefix="/me/saved-articles",
    tags=["saved-articles"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=SavedArticlesResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
    },
)
def list_my_saved_articles(
    user: CurrentUserDep,
    list_saved_articles: ListSavedArticlesDep,
) -> SavedArticlesResponse:
    return SavedArticlesResponse.from_domain(list_saved_articles.execute(user.account_id))


@router.post(
    path="/{article_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=SavedArticleResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
def save_my_article(
    article_id: UUID,
    user: CurrentUserDep,
    save_article: SaveArticleDep,
) -> SavedArticleResponse:
    return SavedArticleResponse.from_domain(
        save_article.execute(user.account_id, article_id)
    )


@router.delete(
    path="/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
def delete_my_saved_article(
    article_id: UUID,
    user: CurrentUserDep,
    delete_saved_article: DeleteSavedArticleDep,
) -> None:
    delete_saved_article.execute(user.account_id, article_id)
