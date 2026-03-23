from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import create_tables


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    create_tables()


app.include_router(api_router, prefix="/api/v1")
