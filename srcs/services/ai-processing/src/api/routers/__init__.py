from fastapi import APIRouter

from src.api.routers.digest.router import router as digest_router
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
# Endpoints the frontend reaches through the gateway: only the digest and its
# chat (ADR-0011). Summaries stay a worker job that writes to Content
# Management (ADR-0010): nobody calls this service to read them.
#
# There is no "/api" prefix here: the browser calls /api/ai-processing/<path>
# and the gateway removes "/api/ai-processing" before forwarding, so this
# service only ever sees its own paths.
#
# Example:
#   browser: POST /api/ai-processing/digest
#   service: POST /digest
# ---------------------------------------------------------------------------
api_routers = APIRouter()
api_routers.include_router(digest_router)
