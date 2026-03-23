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

    Base.metadata.create_all(bind=engine)
    _ensure_runtime_schema_updates()


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


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
