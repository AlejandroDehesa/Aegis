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
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 3
    RAG_MIN_SCORE: float = 0.2
    RAG_MAX_CONTEXT_CHARS: int = 1800
    MEMORY_RECENT_TASK_LIMIT: int = 3
    MEMORY_MAX_CONTEXT_CHARS: int = 1200
    FULL_CONTEXT_MAX_CHARS: int = 2600
    CHROMA_PERSIST_DIRECTORY: str = str(ROOT_DIR / "backend" / "data" / "chroma")
    RAG_VECTOR_COLLECTION: str = "aegis_documents"
    LOCAL_VECTOR_STORE_PATH: str = str(ROOT_DIR / "backend" / "data" / "vector_store.json")


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
        OPENAI_EMBEDDING_MODEL=os.getenv(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        ),
        RAG_CHUNK_SIZE=int(os.getenv("RAG_CHUNK_SIZE", "500")),
        RAG_CHUNK_OVERLAP=int(os.getenv("RAG_CHUNK_OVERLAP", "50")),
        RAG_TOP_K=int(os.getenv("RAG_TOP_K", "3")),
        RAG_MIN_SCORE=float(os.getenv("RAG_MIN_SCORE", "0.2")),
        RAG_MAX_CONTEXT_CHARS=int(os.getenv("RAG_MAX_CONTEXT_CHARS", "1800")),
        MEMORY_RECENT_TASK_LIMIT=int(os.getenv("MEMORY_RECENT_TASK_LIMIT", "3")),
        MEMORY_MAX_CONTEXT_CHARS=int(os.getenv("MEMORY_MAX_CONTEXT_CHARS", "1200")),
        FULL_CONTEXT_MAX_CHARS=int(os.getenv("FULL_CONTEXT_MAX_CHARS", "2600")),
        CHROMA_PERSIST_DIRECTORY=os.getenv(
            "CHROMA_PERSIST_DIRECTORY",
            str(ROOT_DIR / "backend" / "data" / "chroma"),
        ),
        RAG_VECTOR_COLLECTION=os.getenv("RAG_VECTOR_COLLECTION", "aegis_documents"),
        LOCAL_VECTOR_STORE_PATH=os.getenv(
            "LOCAL_VECTOR_STORE_PATH",
            str(ROOT_DIR / "backend" / "data" / "vector_store.json"),
        ),
    )


settings = get_settings()
