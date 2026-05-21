from __future__ import annotations

import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - optional import guard for minimal environments
    Vector = None


def build_embedding_column_type(vector_backend: str, dimension: int) -> sa.types.TypeEngine:
    """Return a SQLAlchemy column type compatible with runtime backend settings.

    - pgvector backend: PostgreSQL VECTOR(dimension), JSON fallback in SQLite tests.
    - non-pgvector backend: JSON for deterministic/local test environments.
    """
    if vector_backend.strip().lower() == "pgvector" and Vector is not None:
        return Vector(dimension).with_variant(sa.JSON(), "sqlite")

    return sa.JSON()
