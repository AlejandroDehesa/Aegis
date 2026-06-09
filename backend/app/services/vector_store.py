from __future__ import annotations

import math
import uuid
from typing import Any

from sqlalchemy import Select, select, text

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk


def _cosine_similarity(first: list[float], second: list[float]) -> float:
    numerator = sum(left * right for left, right in zip(first, second, strict=False))
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))

    if first_norm == 0 or second_norm == 0:
        return 0.0

    return numerator / (first_norm * second_norm)


def _to_float_vector(value: Any) -> list[float] | None:
    if not isinstance(value, list):
        return None

    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{float(value):.12g}" for value in vector) + "]"


def _query_records_pgvector(
    query_embedding: list[float],
    user_id: str,
    top_k: int,
) -> list[dict[str, Any]]:
    query_embedding_literal = _vector_literal(query_embedding)

    sql = text(
        """
        SELECT
            dc.id::text AS id,
            dc.content AS text,
            dc.document_id::text AS document_id,
            d.title AS document_title,
            d.source_name AS source_name,
            dc.chunk_index AS chunk_index,
            1 - (dc.embedding <=> CAST(:query_embedding AS vector)) AS score
        FROM document_chunks AS dc
        JOIN documents AS d ON d.id = dc.document_id
        WHERE dc.user_id = CAST(:user_id AS uuid)
          AND dc.embedding IS NOT NULL
        ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
        LIMIT :top_k
        """
    )

    with SessionLocal() as session:
        rows = session.execute(
            sql,
            {
                "query_embedding": query_embedding_literal,
                "user_id": user_id,
                "top_k": max(top_k, 1),
            },
        ).mappings().all()

    return [
        {
            "id": row["id"],
            "text": row["text"],
            "metadata": {
                "user_id": user_id,
                "document_id": row["document_id"],
                "document_title": row["document_title"] or "Untitled document",
                "source_name": row["source_name"] or "",
                "chunk_index": str(row["chunk_index"]),
            },
            "score": max(0.0, min(1.0, float(row["score"] or 0.0))),
        }
        for row in rows
    ]


def _query_records_local(
    query_embedding: list[float],
    user_id: str,
    top_k: int,
) -> list[dict[str, Any]]:
    user_uuid = uuid.UUID(user_id)
    statement: Select = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.user_id == user_uuid)
        .where(DocumentChunk.embedding.is_not(None))
    )

    with SessionLocal() as session:
        rows = session.execute(statement).all()

    matches: list[dict[str, Any]] = []

    for chunk, document in rows:
        embedding = _to_float_vector(chunk.embedding)
        if embedding is None:
            continue

        score = _cosine_similarity(query_embedding, embedding)
        matches.append(
            {
                "id": str(chunk.id),
                "text": chunk.content,
                "metadata": {
                    "user_id": str(chunk.user_id),
                    "document_id": str(chunk.document_id),
                    "document_title": document.title,
                    "source_name": document.source_name or "",
                    "chunk_index": str(chunk.chunk_index),
                },
                "score": score,
            }
        )

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[: max(top_k, 1)]


def query_records(
    query_embedding: list[float],
    user_id: str,
    top_k: int,
) -> list[dict[str, Any]]:
    backend = settings.RAG_VECTOR_BACKEND.strip().lower()

    if backend == "pgvector":
        return _query_records_pgvector(
            query_embedding=query_embedding,
            user_id=user_id,
            top_k=top_k,
        )

    return _query_records_local(
        query_embedding=query_embedding,
        user_id=user_id,
        top_k=top_k,
    )
