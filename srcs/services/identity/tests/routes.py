"""
URL paths of the identity endpoints, resolved from the app itself.

The routers in src/api/routers are the only place where paths are written.
These constants resolve each route by its name, which defaults to the
endpoint function's name in FastAPI.

If a prefix or path changes, these values update automatically, provided
the route names remain unchanged.
"""

from src.main import app

REGISTER: str = app.url_path_for("register")
LOGIN: str = app.url_path_for("login")
LOGOUT: str = app.url_path_for("logout")
REFRESH: str = app.url_path_for("refresh")
ACCOUNTS_ME: str = app.url_path_for("get_me")
HEALTH: str = app.url_path_for("health_check")
OAUTH_TOKEN: str = app.url_path_for("create_token")
API_KEYS: str = app.url_path_for("create_api_key")
API_KEYS_VERIFY: str = app.url_path_for("verify_api_key")


def api_key(key_id: object) -> str:
    """Path of one key: DELETE /api-keys/{key_id}."""
    return app.url_path_for("revoke_api_key", key_id=str(key_id))
