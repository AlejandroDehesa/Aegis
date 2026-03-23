import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentRead(BaseModel):
    id: uuid.UUID
    title: str
    source_type: str
    source_name: str | None
    chunk_count: int
    content_preview: str
    created_at: datetime
