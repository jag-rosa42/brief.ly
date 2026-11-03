from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.exceptions import RequestValidationError
from shared_errors import ErrorResponse

from src.api.dependencies import GetArticleDep, ListArticlesDep
from src.api.schemas import ArticleListResponse, ArticleResponse

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
)


@router.get(
    path="",
    status_code=status.HTTP_200_OK,
    response_model=ArticleListResponse,
)
def list_articles(
    use_case: ListArticlesDep,
    topic_id: Annotated[str | None, Query()] = None,
    summary: Annotated[Literal["missing"] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=25)] = 25,
) -> ArticleListResponse:
    if (topic_id is None) == (summary is None):
        raise RequestValidationError(
            [
                {
                    "type": "value_error",
                    "loc": ("query",),
                    "msg": "Exactly one of topic_id or summary is required.",
                    "input": None,
                }
            ]
        )

    articles = use_case.execute(
        topic_id=topic_id,
        summary_missing=summary == "missing",
        limit=limit,
    )
    return ArticleListResponse(
        items=[ArticleResponse.from_domain(article) for article in articles]
    )


@router.get(
    path="/{article_id}",
    status_code=status.HTTP_200_OK,
    response_model=ArticleResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
def get_article(article_id: UUID, get_article_use_case: GetArticleDep) -> ArticleResponse:
    return ArticleResponse.from_domain(get_article_use_case.execute(article_id))
