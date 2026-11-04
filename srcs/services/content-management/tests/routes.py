"""
URL paths of the content management endpoints, resolved from the app itself.

The routers in src/api/routers are the only place where paths are written.
These constants resolve each route by its name, which defaults to the
endpoint function's name in FastAPI.

If a prefix or path changes, these values update automatically, provided
the route names remain unchanged.
"""

from uuid import UUID

from src.main import app

ARTICLES: str = app.url_path_for("list_articles")
ARTICLE_DETAIL: str = app.url_path_for(
    "get_article",
    article_id="{article_id}",
)
ARTICLE_SUMMARY: str = app.url_path_for(
    "update_article_summary",
    article_id="{article_id}",
)
HEALTH: str = app.url_path_for("health_check")
INGESTION_RUNS: str = app.url_path_for("create_ingestion_run")
TOPICS: str = app.url_path_for("list_topics")


def article_detail(article_id: UUID | str) -> str:
    return app.url_path_for("get_article", article_id=str(article_id))


def article_summary(article_id: UUID) -> str:
    return app.url_path_for("update_article_summary", article_id=str(article_id))
