from dataclasses import dataclass
import uuid

from app.core.config import settings
from app.services.embeddings_service import generate_embedding
from app.services.vector_store import query_records


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str | None
    document_title: str
    text: str
    score: float


def retrieve_relevant_chunks(
    query: str,
    user_id: uuid.UUID,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    normalized_query = query.strip()

    if not normalized_query:
        return []

    query_embedding = generate_embedding(normalized_query)
    raw_results = query_records(
        query_embedding=query_embedding,
        user_id=str(user_id),
        top_k=top_k or settings.RAG_TOP_K,
    )

    return [
        RetrievedChunk(
            chunk_id=result["id"],
            document_id=result["metadata"].get("document_id"),
            document_title=result["metadata"].get("document_title", "Untitled document"),
            text=result["text"],
            score=float(result.get("score", 0.0)),
        )
        for result in raw_results
    ]


def format_retrieved_context(chunks: list[RetrievedChunk]) -> str | None:
    if not chunks:
        return None

    sections = []

    for index, chunk in enumerate(chunks, start=1):
        sections.append(
            f"[Context {index} | {chunk.document_title} | score={chunk.score:.2f}]\n"
            f"{chunk.text}"
        )

    return "\n\n".join(sections)
