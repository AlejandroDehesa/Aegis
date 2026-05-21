from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


class Base(DeclarativeBase):
    pass


engine = create_engine(
    _normalize_database_url(settings.DATABASE_URL),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def create_tables() -> None:
    import app.models  # noqa: F401

    _ensure_pgvector_extension()
    Base.metadata.create_all(bind=engine)
    _ensure_runtime_schema_updates()


def _ensure_pgvector_extension() -> None:
    if engine.dialect.name != "postgresql":
        return

    if settings.RAG_VECTOR_BACKEND != "pgvector":
        return

    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    except Exception as error:
        raise RuntimeError(
            "RAG_VECTOR_BACKEND=pgvector requires PostgreSQL pgvector extension "
            "(CREATE EXTENSION vector)."
        ) from error


def _ensure_runtime_schema_updates() -> None:
    if engine.dialect.name != "postgresql":
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ADD COLUMN IF NOT EXISTS execution_trace JSONB "
                "NOT NULL DEFAULT '[]'::jsonb"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ADD COLUMN IF NOT EXISTS finished_at TIMESTAMPTZ"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ADD COLUMN IF NOT EXISTS duration_ms INTEGER"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ADD COLUMN IF NOT EXISTS feedback_rating INTEGER"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ADD COLUMN IF NOT EXISTS feedback_comment TEXT"
            )
        )
        connection.execute(
            text(
                "ALTER TABLE tasks "
                "ADD COLUMN IF NOT EXISTS feedback_submitted_at TIMESTAMPTZ"
            )
        )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
