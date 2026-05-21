import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.services.embeddings_service import generate_embeddings


class DocumentIngestionError(Exception):
    pass


class DocumentValidationError(DocumentIngestionError):
    pass


class DocumentNotFoundError(DocumentIngestionError):
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

    for index, (chunk_text, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
        chunk = DocumentChunk(
            document_id=document.id,
            user_id=user_id,
            chunk_index=index,
            content=chunk_text,
            char_count=len(chunk_text),
            embedding=embedding,
        )
        db.add(chunk)
        chunk_models.append(chunk)

    try:
        db.commit()
    except Exception as error:
        db.rollback()
        raise DocumentIngestionError("Document ingestion failed.") from error

    document.chunks = chunk_models
    db.refresh(document)
    return document


def list_documents_for_user(*, db: Session, user_id: uuid.UUID) -> list[Document]:
    return db.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
    ).scalars().all()


def delete_document_for_user(
    *,
    db: Session,
    user_id: uuid.UUID,
    document_id: uuid.UUID,
) -> None:
    document = db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == user_id,
        )
    ).scalar_one_or_none()

    if document is None:
        raise DocumentNotFoundError("Document not found.")

    try:
        db.delete(document)
        db.commit()
    except Exception as error:
        db.rollback()
        raise DocumentIngestionError("Document deletion failed.") from error
