import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class TaskFeedbackUpdate(BaseModel):
    feedback_rating: int = Field(ge=1, le=5)
    feedback_comment: str | None = Field(default=None, max_length=1200)


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
    memory_task_count: int = 0
    context_preview: str | None = None
    memory_context_preview: str | None = None
    full_context_preview: str | None = None
    context_truncated: bool = False
    memory_context_truncated: bool = False
    full_context_truncated: bool = False
    retrieval_error: str | None = None


class TaskExecutionStepRead(BaseModel):
    step_index: int | None = None
    step_number: int | None = None
    step_name: str
    agent_name: str
    status: str
    short_summary: str | None = None
    result_preview: str | None = None
    used_previous_output: bool = False
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    error_message: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_prompt_tokens: int | None = None
    llm_completion_tokens: int | None = None
    llm_total_tokens: int | None = None
    llm_estimated_cost: float | None = None
    llm_fallback_used: bool | None = None
    llm_error: str | None = None
    llm_retry_count: int | None = None
    llm_latency_ms: int | None = None
    llm_usage_summary: dict[str, object] | None = None


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
    execution_trace: list[TaskExecutionStepRead] = Field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    executed_at: datetime | None = None
    error_message: str | None = None
    feedback_rating: int | None = None
    feedback_comment: str | None = None
    feedback_submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    rag_debug: TaskRagDebugRead | None = None


class TaskTraceRead(BaseModel):
    task_id: uuid.UUID
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: int | None = None
    execution_trace: list[TaskExecutionStepRead] = Field(default_factory=list)
