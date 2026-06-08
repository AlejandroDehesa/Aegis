from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings


def _normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    return database_url


class Base(DeclarativeBase):
    pass


def _build_engine_options(database_url: str) -> dict[str, object]:
    options: dict[str, object] = {
        "pool_pre_ping": True,
    }

    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            options["poolclass"] = StaticPool

    return options


normalized_database_url = _normalize_database_url(settings.DATABASE_URL)
engine = create_engine(
    normalized_database_url,
    **_build_engine_options(normalized_database_url),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def create_test_schema() -> None:
    if settings.APP_ENV != "test":
        raise RuntimeError("create_test_schema() is only available when APP_ENV=test.")

    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

def reset_test_schema() -> None:
    if settings.APP_ENV != "test":
        raise RuntimeError("reset_test_schema() is only available when APP_ENV=test.")

    import app.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


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
