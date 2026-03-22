import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    PROJECT_NAME: str = "Aegis Backend"
    DATABASE_URL: str = Field(min_length=1)
    JWT_SECRET_KEY: str = Field(min_length=1)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-5-mini"


@lru_cache
def get_settings() -> Settings:
    return Settings(
        PROJECT_NAME=os.getenv("PROJECT_NAME", "Aegis Backend"),
        DATABASE_URL=os.getenv("DATABASE_URL", ""),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", ""),
        JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", "HS256"),
        ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        OPENAI_API_KEY=os.getenv("OPENAI_API_KEY") or None,
        OPENAI_MODEL=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
    )


settings = get_settings()
