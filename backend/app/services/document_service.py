import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.services.embeddings_service import generate_embeddings
from app.services.vector_store import VectorStoreRecord, add_records, delete_records


class DocumentIngestionError(Exception):
    pass


class DocumentValidationError(DocumentIngestionError):
    pass


def _normalize_content(content: str) -> str:
    return content.strip()


def _chunk_text(text: str) -> list[str]:
    normalized_text = " ".join(text.split())

    if not normalized_text:
        return []

    chunk_size = settings.RAG_CHUNK_SIZE
    overlap = min(settings.RAG_CHUNK_OVERLAP, max(0, chunk_size - 1))
    chunks: list[str] = []
    start = 0

    while start < len(normalized_text):
        end = min(start + chunk_size, len(normalized_text))

        if end < len(normalized_text):
            boundary = normalized_text.rfind(" ", start, end)
            if boundary > start + (chunk_size // 2):
                end = boundary

        chunk = normalized_text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized_text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def create_document(
    *,
    db: Session,
    user_id: uuid.UUID,
    title: str,
    content: str,
    source_type: str,
    source_name: str | None = None,
) -> Document:
    normalized_title = title.strip()
    normalized_content = _normalize_content(content)

    if not normalized_title:
        raise DocumentValidationError("Document title is required.")

    if not normalized_content:
        raise DocumentValidationError("Document content cannot be empty.")

    chunks = _chunk_text(normalized_content)

    if not chunks:
        raise DocumentValidationError("Document content could not be chunked.")

    embeddings = generate_embeddings(chunks)
    document = Document(
        user_id=user_id,
        title=normalized_title,
        source_type=source_type,
        source_name=source_name,
        content=normalized_content,
    )

    db.add(document)
    db.flush()

    chunk_models: list[DocumentChunk] = []
    vector_records: list[VectorStoreRecord] = []

    for index, (chunk_text, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        chunk = DocumentChunk(
            document_id=document.id,
            user_id=user_id,
            chunk_index=index,
            content=chunk_text,
            char_count=len(chunk_text),
        )
        db.add(chunk)
        db.flush()
        chunk_models.append(chunk)
        vector_records.append(
            VectorStoreRecord(
                id=str(chunk.id),
                text=chunk_text,
                embedding=embedding,
                metadata={
                    "user_id": str(user_id),
                    "document_id": str(document.id),
                    "document_title": document.title,
                    "chunk_index": str(index),
                },
            )
        )

    created_ids = [record.id for record in vector_records]

    try:
        add_records(vector_records)
        db.commit()
    except Exception as error:
        db.rollback()
        try:
            delete_records(created_ids)
        except Exception:
            pass
        raise DocumentIngestionError("Document ingestion failed.") from error

    document.chunks = chunk_models
    db.refresh(document)
    return document
