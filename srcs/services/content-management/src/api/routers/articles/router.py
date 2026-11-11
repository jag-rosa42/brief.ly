from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.exceptions import RequestValidationError
from shared_errors import ErrorResponse

from src.api.dependencies import (
    GetArticleDep,
    ListArticlesDep,
    UpdateArticleSummaryDep,
)
from src.api.dependencies.service_auth import ARTICLES_READ, SUMMARIES_WRITE
from src.api.schemas import (
    ArticleListResponse,
    ArticleResponse,
    UpdateArticleSummaryRequest,
)

router = APIRouter(
    prefix="/articles",
    tags=["articles"],
)


@router.get(
    path="",
    dependencies=[ARTICLES_READ],
    status_code=status.HTTP_200_OK,
    response_model=ArticleListResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
def list_articles(
    list_articles: ListArticlesDep,
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

    articles = list_articles.execute(
        topic_id=topic_id,
        summary_missing=summary == "missing",
        limit=limit,
    )
    return ArticleListResponse(
        items=[ArticleResponse.from_domain(article) for article in articles]
    )


@router.get(
    path="/{article_id}",
    dependencies=[ARTICLES_READ],
    status_code=status.HTTP_200_OK,
    response_model=ArticleResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
def get_article(article_id: UUID, get_article: GetArticleDep) -> ArticleResponse:
    return ArticleResponse.from_domain(get_article.execute(article_id))


@router.put(
    path="/{article_id}/summary",
    dependencies=[SUMMARIES_WRITE],
    status_code=status.HTTP_200_OK,
    response_model=ArticleResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)
def update_article_summary(
    article_id: UUID,
    body: UpdateArticleSummaryRequest,
    update_article_summary: UpdateArticleSummaryDep,
) -> ArticleResponse:
    article = update_article_summary.execute(
        article_id=article_id,
        text=body.text,
        llm_model=body.llm_model,
        rejected=body.rejected,
        quality_comment=body.quality_comment,
        generation_duration_ms=body.generation_duration_ms,
    )
    return ArticleResponse.from_domain(article)
