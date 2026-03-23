from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.document import DocumentRead
from app.services.document_service import (
    DocumentIngestionError,
    DocumentValidationError,
    create_document,
)


router = APIRouter()


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
        source_name = file.filename

        try:
            document_content = (await file.read()).decode("utf-8").strip()
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

    return DocumentRead(
        id=document.id,
        title=document.title,
        source_type=document.source_type,
        source_name=document.source_name,
        chunk_count=len(document.chunks),
        content_preview=document.content[:200],
        created_at=document.created_at,
    )
