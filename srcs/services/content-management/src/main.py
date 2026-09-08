from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import api_routers, root_routers
from src.infrastructure.database.config import settings

app = FastAPI(title=settings.PROJECT_NAME)

# Allow the configured frontend origin(s) to call this API from the browser.
# Without this, the browser blocks cross-origin requests
app.add_middleware(
    middleware_class=CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(root_routers)
app.include_router(api_routers)

