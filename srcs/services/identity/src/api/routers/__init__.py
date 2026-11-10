from fastapi import APIRouter

from src.api.routers.accounts.router import router as account_router
from src.api.routers.api_keys.internal_router import router as api_key_verify_router
from src.api.routers.api_keys.router import router as api_key_router
from src.api.routers.auth.router import router as auth_router
from src.api.routers.health.router import router as health_router
from src.api.routers.oauth.router import router as oauth_router

# ---------------------------------------------------------------------------
# Root-level endpoints
# ---------------------------------------------------------------------------
# Endpoints registered here are exposed directly at the application root,
# without the /api prefix.
#
# Example:
#   health_router -> GET /health
# ---------------------------------------------------------------------------
root_routers = APIRouter()
root_routers.include_router(health_router)


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
# Endpoints the frontend reaches through the gateway.
#
# There is no "/api" prefix here: the browser calls /api/identity/<path> and
# the gateway removes "/api/identity" before forwarding, so this service only
# ever sees its own paths.
#
# Example:
#   browser: POST /api/identity/auth/login
#   service: POST /auth/login
# ---------------------------------------------------------------------------
api_routers = APIRouter()
api_routers.include_router(auth_router)
api_routers.include_router(account_router)
api_routers.include_router(api_key_router)


# ---------------------------------------------------------------------------
# Internal endpoints
# ---------------------------------------------------------------------------
# Called by other services only, directly on the backend network
# (docs/api/00_conventions.md). The gateway's allowlist never routes
# /internal (ADR-0006), so the browser can't reach them.
#
# Example:
#   personalization: POST http://identity:8000/internal/v1/oauth/token
#   gateway (ForwardAuth): GET http://identity:8000/internal/v1/api-keys/verify
# ---------------------------------------------------------------------------
internal_routers = APIRouter(prefix="/internal/v1")
internal_routers.include_router(oauth_router)
internal_routers.include_router(api_key_verify_router)
