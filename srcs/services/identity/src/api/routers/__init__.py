from fastapi import APIRouter

from src.api.routers.auth.router import router as auth_router

api_routers = APIRouter(prefix="/api")

api_routers.include_router(auth_router)
