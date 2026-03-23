from fastapi import APIRouter

from app.api.v1.agents import router as agents_router
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.tasks import router as tasks_router


api_router = APIRouter()
api_router.include_router(agents_router, tags=["agents"])
api_router.include_router(auth_router, tags=["auth"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(tasks_router, tags=["tasks"])
