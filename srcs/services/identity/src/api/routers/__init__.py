from fastapi import APIRouter

from src.api.routers.accounts.router import router as account_router
from src.api.routers.auth.router import router as auth_router
from src.api.routers.health.router import router as health_router

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
# All routers registered here are exposed under the /api prefix.
#
# Example:
#   auth_router -> POST /api/auth/...
# ---------------------------------------------------------------------------
api_routers = APIRouter(prefix="/api")
api_routers.include_router(auth_router)
api_routers.include_router(account_router)
