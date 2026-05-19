from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_database_connection

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, object]:
    db_ready = check_database_connection()
    return {
        "status": "ok",
        "service": "aegis-backend",
        "environment": settings.APP_ENV,
        "database_reachable": db_ready,
    }


@router.get("/health/live")
def health_live() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "aegis-backend",
    }


@router.get("/health/ready")
def health_ready() -> dict[str, object]:
    db_ready = check_database_connection()
    payload = {
        "status": "ready" if db_ready else "not_ready",
        "service": "aegis-backend",
        "checks": {
            "database": db_ready,
            "config_loaded": bool(settings.DATABASE_URL and settings.JWT_SECRET_KEY),
        },
    }
    if not db_ready:
        return JSONResponse(status_code=503, content=payload)  # type: ignore[return-value]
    return payload
