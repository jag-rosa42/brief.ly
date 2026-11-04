from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from fastapi.exceptions import RequestValidationError

from src.api.dependencies import ListArticlesDep
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
