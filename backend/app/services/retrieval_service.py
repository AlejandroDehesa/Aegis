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
    source_name: str | None
    chunk_index: int | None
    text: str
    score: float


@dataclass
class ContextBuildResult:
    text: str | None
    used_chunks: list[RetrievedChunk]
    truncated: bool


CONTEXT_START_DELIMITER = "=== RETRIEVED CONTEXT START ==="
CONTEXT_END_DELIMITER = "=== RETRIEVED CONTEXT END ==="
CONTEXT_SECTION_DELIMITER = "\n\n---\n\n"


def _parse_chunk_index(value: str | None) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def retrieve_relevant_chunks(
    query: str,
    user_id: uuid.UUID,
    top_k: int | None = None,
    min_score: float | None = None,
) -> list[RetrievedChunk]:
    normalized_query = query.strip()

    if not normalized_query:
        return []

    requested_top_k = top_k or settings.RAG_TOP_K
    score_threshold = settings.RAG_MIN_SCORE if min_score is None else min_score
    query_embedding = generate_embedding(normalized_query)
    user_id_str = str(user_id)
    raw_results = query_records(
        query_embedding=query_embedding,
        user_id=user_id_str,
        top_k=max(requested_top_k * 3, requested_top_k),
    )

    chunks: list[RetrievedChunk] = []
    for result in raw_results:
        metadata = result.get("metadata", {}) or {}
        record_user_id = str(metadata.get("user_id", "") or "").strip()
        if record_user_id and record_user_id != user_id_str:
            continue

        chunks.append(
            RetrievedChunk(
                chunk_id=result["id"],
                document_id=metadata.get("document_id"),
                document_title=metadata.get("document_title", "Untitled document"),
                source_name=metadata.get("source_name") or None,
                chunk_index=_parse_chunk_index(metadata.get("chunk_index")),
                text=result["text"],
                score=float(result.get("score", 0.0)),
            )
        )

    filtered_chunks = [chunk for chunk in chunks if chunk.score >= score_threshold]
    return filtered_chunks[:requested_top_k]


def _format_chunk_section(index: int, chunk: RetrievedChunk, text: str) -> str:
    source_label = chunk.source_name or "N/A"
    chunk_index_label = chunk.chunk_index if chunk.chunk_index is not None else "N/A"

    return (
        f"[Chunk {index}]\n"
        f"Document: {chunk.document_title}\n"
        f"Source: {source_label}\n"
        f"Chunk Index: {chunk_index_label}\n"
        f"Score: {chunk.score:.2f}\n"
        "Content:\n"
        f"{text}"
    )


def _truncate_chunk_text(
    chunk: RetrievedChunk,
    chunk_number: int,
    available_chars: int,
) -> str | None:
    ellipsis = "\n..."
    header = _format_chunk_section(chunk_number, chunk, "")
    content_prefix = "" if header.endswith("\n") else "\n"
    header_length = len(header) + len(content_prefix)

    if available_chars <= header_length + len(ellipsis) + 40:
        return None

    remaining_chars = available_chars - header_length - len(ellipsis)
    truncated_text = chunk.text[:remaining_chars].rstrip()

    if not truncated_text:
        return None

    return _format_chunk_section(
        chunk_number,
        chunk,
        f"{truncated_text}{ellipsis}",
    )


def build_context(
    chunks: list[RetrievedChunk],
    max_chars: int | None = None,
) -> ContextBuildResult:
    if not chunks:
        return ContextBuildResult(text=None, used_chunks=[], truncated=False)

    max_context_chars = max_chars or settings.RAG_MAX_CONTEXT_CHARS
    sections: list[str] = []
    used_chunks: list[RetrievedChunk] = []
    truncated = False
    current_length = len(CONTEXT_START_DELIMITER) + len(CONTEXT_END_DELIMITER) + 2

    for index, chunk in enumerate(chunks, start=1):
        section = _format_chunk_section(index, chunk, chunk.text)
        separator_length = len(CONTEXT_SECTION_DELIMITER) if sections else 0
        projected_length = current_length + separator_length + len(section)

        if projected_length <= max_context_chars:
            if sections:
                current_length += len(CONTEXT_SECTION_DELIMITER)
            sections.append(section)
            used_chunks.append(chunk)
            current_length += len(section)
            continue

        remaining_chars = max_context_chars - current_length - separator_length
        truncated_section = _truncate_chunk_text(chunk, index, remaining_chars)

        if truncated_section:
            if sections:
                current_length += len(CONTEXT_SECTION_DELIMITER)
            sections.append(truncated_section)
            truncated_text = truncated_section.split("Content:\n", maxsplit=1)[-1]
            used_chunks.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    source_name=chunk.source_name,
                    chunk_index=chunk.chunk_index,
                    text=truncated_text,
                    score=chunk.score,
                )
            )
            current_length += len(truncated_section)

        truncated = True
        break

    if not sections:
        return ContextBuildResult(text=None, used_chunks=[], truncated=truncated)

    context_body = CONTEXT_SECTION_DELIMITER.join(sections)
    return ContextBuildResult(
        text=f"{CONTEXT_START_DELIMITER}\n{context_body}\n{CONTEXT_END_DELIMITER}",
        used_chunks=used_chunks,
        truncated=truncated,
    )


def format_retrieved_context(chunks: list[RetrievedChunk]) -> str | None:
    return build_context(chunks).text
