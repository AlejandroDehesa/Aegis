import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    title: str
    description: str | None = None


class TaskRagChunkRead(BaseModel):
    chunk_id: str
    document_id: str | None = None
    document_title: str
    source_name: str | None = None
    chunk_index: int | None = None
    score: float
    text: str


class TaskRagDebugRead(BaseModel):
    query: str
    top_k: int
    min_score: float
    retrieved_chunks: list[TaskRagChunkRead]
    context_preview: str | None = None
    context_truncated: bool = False
    retrieval_error: str | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None
    status: str
    task_type: str
    agent_name: str
    result_text: str | None = None
    executed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    rag_debug: TaskRagDebugRead | None = None
