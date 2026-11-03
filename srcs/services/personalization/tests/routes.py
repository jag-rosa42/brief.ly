"""
URL paths of the personalization endpoints, resolved from the app itself.

The routers in src/api/routers are the only place where paths are written.
These constants resolve each route by its name, which defaults to the
endpoint function's name in FastAPI.

If a prefix or path changes, these values update automatically, provided
the route names remain unchanged.
"""

from uuid import UUID

from src.main import app

HEALTH: str = app.url_path_for("health_check")
INTERNAL_ME_PROFILE: str = app.url_path_for("get_my_internal_profile")
ME_PROFILE: str = app.url_path_for("get_my_profile")
ME_SAVED_ARTICLES: str = app.url_path_for("list_my_saved_articles")
TOPICS: str = app.url_path_for("get_topics")


def me_saved_article(article_id: UUID) -> str:
    return app.url_path_for("delete_my_saved_article", article_id=str(article_id))
