import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.document_service import (
    DocumentIngestionError,
    DocumentNotFoundError,
    DocumentValidationError,
    create_document,
    delete_document_for_user,
    list_documents_for_user,
)


router = APIRouter()


def _sanitize_filename(raw_filename: str | None) -> str | None:
    if not raw_filename:
        return None

    normalized = raw_filename.strip().replace("\\", "/")
    if "/" in normalized or ".." in normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name.",
        )

    sanitized = Path(normalized).name.strip()
    if not sanitized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file name.",
        )

    return sanitized


def _validate_upload_file(file: UploadFile, file_bytes: bytes) -> str:
    file_name = _sanitize_filename(file.filename)
    if not file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    max_bytes = max(settings.DOCUMENT_MAX_UPLOAD_MB, 1) * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Uploaded file exceeds the {settings.DOCUMENT_MAX_UPLOAD_MB}MB limit.",
        )

    extension = Path(file_name).suffix.lower()
    if extension not in {ext.lower() for ext in settings.DOCUMENT_ALLOWED_EXTENSIONS}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{extension or '<none>'}' is not allowed.",
        )

    mime_type = (file.content_type or "").lower()
    if mime_type and mime_type not in {value.lower() for value in settings.DOCUMENT_ALLOWED_MIME_TYPES}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File MIME type '{mime_type}' is not allowed.",
        )

    if extension == ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF uploads are reserved for future parser support.",
        )

    return file_name


def _serialize_document(document: Document) -> DocumentRead:
    return DocumentRead(
        id=document.id,
        title=document.title,
        source_type=document.source_type,
        source_name=document.source_name,
        chunk_count=len(document.chunks),
        content_preview=document.content[:200],
        created_at=document.created_at,
    )


@router.post("/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    title: str | None = Form(None),
    content: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    if content and file is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either raw content or a file, not both.",
        )

    source_type = "text"
    source_name = None
    document_content = (content or "").strip()

    if file is not None:
        source_type = "file"
        raw_bytes = await file.read()
        source_name = _validate_upload_file(file, raw_bytes)

        try:
            document_content = raw_bytes.decode("utf-8").strip()
        except UnicodeDecodeError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only UTF-8 text files are supported.",
            ) from error

    if not document_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content is required.",
        )

    document_title = (title or source_name or "Untitled document").strip()

    try:
        document = create_document(
            db=db,
            user_id=current_user.id,
            title=document_title,
            content=document_content,
            source_type=source_type,
            source_name=source_name,
        )
    except DocumentValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except DocumentIngestionError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    return _serialize_document(document)


@router.get("/documents", response_model=list[DocumentRead])
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    documents = list_documents_for_user(
        db=db,
        user_id=current_user.id,
    )
    return [_serialize_document(document) for document in documents]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    try:
        delete_document_for_user(
            db=db,
            user_id=current_user.id,
            document_id=document_id,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except DocumentIngestionError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)
