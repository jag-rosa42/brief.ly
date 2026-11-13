"""
URL paths of the AI processing endpoints, resolved from the app itself.

The routers in src/api/routers are the only place where paths are written.
These constants resolve each route by its name, which defaults to the
endpoint function's name in FastAPI.

If a prefix or path changes, these values update automatically, provided
the route names remain unchanged.
"""

from src.main import app

HEALTH: str = app.url_path_for("health_check")
DIGEST: str = app.url_path_for("write_digest")
DIGEST_CHAT: str = app.url_path_for("answer_question")
