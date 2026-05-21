import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


ROOT_DIR = Path(__file__).resolve().parents[3]
load_dotenv(ROOT_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    PROJECT_NAME: str = "Aegis Backend"
    APP_ENV: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENABLE_REQUEST_LOGGING: bool = True
    PORT: int = 8000
    DATABASE_URL: str = Field(min_length=1)
    JWT_SECRET_KEY: str = Field(min_length=1)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-5-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_PROVIDER: str = "template"
    LLM_ENABLE_REAL_CALLS: bool = False
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_TOKENS: int = 1200
    LLM_TEMPERATURE: float = 0.3
    LLM_RETRY_ATTEMPTS: int = 1
    LLM_RETRY_BACKOFF_SECONDS: float = 0.5
    LLM_REQUEST_HARD_MAX_TOKENS: int = 2000
    LLM_TASK_TOTAL_TOKEN_SOFT_LIMIT: int = 6000
    LLM_TASK_TOTAL_TOKEN_HARD_LIMIT: int = 10000
    LLM_ENABLE_COST_ESTIMATION: bool = True
    LLM_COST_PER_1M_INPUT_TOKENS: float | None = None
    LLM_COST_PER_1M_OUTPUT_TOKENS: float | None = None
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_MODEL: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_SITE_URL: str | None = "http://localhost:5173"
    OPENROUTER_APP_NAME: str | None = "Aegis"
    TASK_EXECUTION_MODE: str = "background"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120
    RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE: int = 20
    RATE_LIMIT_TASK_EXECUTE_PER_MINUTE: int = 10
    DOCUMENT_MAX_UPLOAD_MB: int = 5
    DOCUMENT_ALLOWED_EXTENSIONS: list[str] = [".txt", ".md"]
    DOCUMENT_ALLOWED_MIME_TYPES: list[str] = ["text/plain", "text/markdown"]
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_ENABLED: bool = True
    RAG_VECTOR_BACKEND: str = "pgvector"
    EMBEDDING_DIMENSION: int = 64
    RAG_TOP_K: int = 3
    RAG_MIN_SCORE: float = 0.2
    RAG_MAX_CONTEXT_CHARS: int = 1800
    RAG_TRACE_SNIPPET_CHARS: int = 300
    MEMORY_RECENT_TASK_LIMIT: int = 3
    MEMORY_MAX_CONTEXT_CHARS: int = 1200
    FULL_CONTEXT_MAX_CHARS: int = 2600
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]
    FRONTEND_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ]
    CHROMA_PERSIST_DIRECTORY: str = str(ROOT_DIR / "backend" / "data" / "chroma")
    RAG_VECTOR_COLLECTION: str = "aegis_documents"
    LOCAL_VECTOR_STORE_PATH: str = str(ROOT_DIR / "backend" / "data" / "vector_store.json")


@lru_cache
def get_settings() -> Settings:
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            os.getenv(
                "FRONTEND_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173",
            ),
        ).split(",")
        if origin.strip()
    ]

    resolved = Settings(
        PROJECT_NAME=os.getenv("PROJECT_NAME", "Aegis Backend"),
        APP_ENV=os.getenv("APP_ENV", "development").strip().lower(),
        DEBUG=_env_bool("DEBUG", False),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        ENABLE_REQUEST_LOGGING=_env_bool("ENABLE_REQUEST_LOGGING", True),
        PORT=int(os.getenv("PORT", "8000")),
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
        LLM_PROVIDER=os.getenv("LLM_PROVIDER", "template"),
        LLM_ENABLE_REAL_CALLS=_env_bool("LLM_ENABLE_REAL_CALLS", False),
        LLM_TIMEOUT_SECONDS=int(os.getenv("LLM_TIMEOUT_SECONDS", "30")),
        LLM_MAX_TOKENS=int(os.getenv("LLM_MAX_TOKENS", "1200")),
        LLM_TEMPERATURE=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        LLM_RETRY_ATTEMPTS=int(os.getenv("LLM_RETRY_ATTEMPTS", "1")),
        LLM_RETRY_BACKOFF_SECONDS=float(os.getenv("LLM_RETRY_BACKOFF_SECONDS", "0.5")),
        LLM_REQUEST_HARD_MAX_TOKENS=int(os.getenv("LLM_REQUEST_HARD_MAX_TOKENS", "2000")),
        LLM_TASK_TOTAL_TOKEN_SOFT_LIMIT=int(os.getenv("LLM_TASK_TOTAL_TOKEN_SOFT_LIMIT", "6000")),
        LLM_TASK_TOTAL_TOKEN_HARD_LIMIT=int(os.getenv("LLM_TASK_TOTAL_TOKEN_HARD_LIMIT", "10000")),
        LLM_ENABLE_COST_ESTIMATION=_env_bool("LLM_ENABLE_COST_ESTIMATION", True),
        LLM_COST_PER_1M_INPUT_TOKENS=(
            float(os.getenv("LLM_COST_PER_1M_INPUT_TOKENS"))
            if os.getenv("LLM_COST_PER_1M_INPUT_TOKENS") not in {None, ""}
            else None
        ),
        LLM_COST_PER_1M_OUTPUT_TOKENS=(
            float(os.getenv("LLM_COST_PER_1M_OUTPUT_TOKENS"))
            if os.getenv("LLM_COST_PER_1M_OUTPUT_TOKENS") not in {None, ""}
            else None
        ),
        OPENROUTER_API_KEY=os.getenv("OPENROUTER_API_KEY") or None,
        OPENROUTER_MODEL=os.getenv("OPENROUTER_MODEL") or None,
        OPENROUTER_BASE_URL=os.getenv(
            "OPENROUTER_BASE_URL",
            "https://openrouter.ai/api/v1",
        ),
        OPENROUTER_SITE_URL=os.getenv("OPENROUTER_SITE_URL") or None,
        OPENROUTER_APP_NAME=os.getenv("OPENROUTER_APP_NAME") or None,
        TASK_EXECUTION_MODE=os.getenv("TASK_EXECUTION_MODE", "background").strip().lower(),
        RATE_LIMIT_ENABLED=_env_bool("RATE_LIMIT_ENABLED", True),
        RATE_LIMIT_REQUESTS_PER_MINUTE=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "120")),
        RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE=int(
            os.getenv("RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE", "20")
        ),
        RATE_LIMIT_TASK_EXECUTE_PER_MINUTE=int(
            os.getenv("RATE_LIMIT_TASK_EXECUTE_PER_MINUTE", "10")
        ),
        DOCUMENT_MAX_UPLOAD_MB=int(os.getenv("DOCUMENT_MAX_UPLOAD_MB", "5")),
        DOCUMENT_ALLOWED_EXTENSIONS=[
            value.strip().lower()
            for value in os.getenv("DOCUMENT_ALLOWED_EXTENSIONS", ".txt,.md").split(",")
            if value.strip()
        ],
        DOCUMENT_ALLOWED_MIME_TYPES=[
            value.strip().lower()
            for value in os.getenv(
                "DOCUMENT_ALLOWED_MIME_TYPES",
                "text/plain,text/markdown",
            ).split(",")
            if value.strip()
        ],
        RAG_CHUNK_SIZE=int(os.getenv("RAG_CHUNK_SIZE", "500")),
        RAG_CHUNK_OVERLAP=int(os.getenv("RAG_CHUNK_OVERLAP", "50")),
        RAG_ENABLED=_env_bool("RAG_ENABLED", True),
        RAG_VECTOR_BACKEND=os.getenv("RAG_VECTOR_BACKEND", "pgvector").strip().lower(),
        EMBEDDING_DIMENSION=int(os.getenv("EMBEDDING_DIMENSION", "64")),
        RAG_TOP_K=int(os.getenv("RAG_TOP_K", "3")),
        RAG_MIN_SCORE=float(os.getenv("RAG_MIN_SCORE", "0.2")),
        RAG_MAX_CONTEXT_CHARS=int(os.getenv("RAG_MAX_CONTEXT_CHARS", "1800")),
        RAG_TRACE_SNIPPET_CHARS=int(os.getenv("RAG_TRACE_SNIPPET_CHARS", "300")),
        MEMORY_RECENT_TASK_LIMIT=int(os.getenv("MEMORY_RECENT_TASK_LIMIT", "3")),
        MEMORY_MAX_CONTEXT_CHARS=int(os.getenv("MEMORY_MAX_CONTEXT_CHARS", "1200")),
        FULL_CONTEXT_MAX_CHARS=int(os.getenv("FULL_CONTEXT_MAX_CHARS", "2600")),
        CORS_ORIGINS=cors_origins,
        FRONTEND_ORIGINS=cors_origins,
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
    _validate_runtime_settings(resolved)
    return resolved


def _validate_runtime_settings(config: Settings) -> None:
    if config.EMBEDDING_DIMENSION <= 0:
        raise ValueError("EMBEDDING_DIMENSION must be greater than zero.")

    if config.RAG_VECTOR_BACKEND not in {"pgvector", "local"}:
        raise ValueError("RAG_VECTOR_BACKEND must be one of: pgvector, local.")

    if config.APP_ENV in {"production", "prod"}:
        weak_secret_values = {
            "change-this-secret-in-production",
            "changeme",
            "secret",
            "default",
        }
        normalized_secret = config.JWT_SECRET_KEY.strip().lower()
        if len(config.JWT_SECRET_KEY) < 32 or normalized_secret in weak_secret_values:
            raise ValueError(
                "JWT_SECRET_KEY must be a strong secret (>=32 chars) when APP_ENV=production."
            )


settings = get_settings()
