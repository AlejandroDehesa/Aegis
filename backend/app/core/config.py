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


@lru_cache
def get_settings() -> Settings:
    return Settings(
        PROJECT_NAME=os.getenv("PROJECT_NAME", "Aegis Backend"),
        DATABASE_URL=os.getenv("DATABASE_URL", ""),
    )


settings = get_settings()
