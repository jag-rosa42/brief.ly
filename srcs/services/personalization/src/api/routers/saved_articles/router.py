from uuid import UUID

from fastapi import APIRouter, status
from shared_errors import ErrorResponse

from src.api.dependencies import (
    CurrentAccountIdDep,
    DeleteSavedArticleDep,
    ListSavedArticlesDep,
)
from src.api.schemas.saved_article import SavedArticlesResponse

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
    account_id: CurrentAccountIdDep,
    list_saved_articles: ListSavedArticlesDep,
) -> SavedArticlesResponse:
    return SavedArticlesResponse.from_domain(list_saved_articles.execute(account_id))


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
    account_id: CurrentAccountIdDep,
    delete_saved_article: DeleteSavedArticleDep,
) -> None:
    delete_saved_article.execute(account_id, article_id)
