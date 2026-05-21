"""add pgvector embeddings to document chunks

Revision ID: 0002_pgvector_document_chunk_embeddings
Revises: 0001_initial_schema
Create Date: 2026-05-21 18:10:00
"""
from __future__ import annotations

import os

from alembic import op
import sqlalchemy as sa


revision = "0002_pgvector_document_chunk_embeddings"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def _embedding_dimension() -> int:
    raw = os.getenv("EMBEDDING_DIMENSION", "64")
    try:
        value = int(raw)
    except ValueError:
        value = 64
    return value if value > 0 else 64


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    dimension = _embedding_dimension()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        f"ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS embedding vector({dimension})"
    )
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_cosine
                ON document_chunks USING hnsw (embedding vector_cosine_ops);
            EXCEPTION WHEN feature_not_supported OR undefined_object THEN
                NULL;
            END;
        END
        $$;
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_cosine")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding")
