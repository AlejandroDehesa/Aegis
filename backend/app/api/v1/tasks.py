import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskExecutionStepRead,
    TaskFeedbackUpdate,
    TaskRagChunkRead,
    TaskRagDebugRead,
    TaskRead,
    TaskTraceRead,
)
from app.services.agent_selector import select_agent
from app.services.task_classifier import classify_task
from app.services.task_executor import (
    TaskExecutionError,
    TaskExecutionResult,
    TaskExecutionStateError,
    execute_task,
    get_task_execution_mode,
    queue_task_for_background,
    run_task_execution_background,
)


router = APIRouter()


def _normalize_trace_step(raw_step: Any, fallback_agent_name: str) -> dict[str, Any]:
    if not isinstance(raw_step, dict):
        return {
            "step_name": "execution",
            "agent_name": fallback_agent_name,
            "status": "completed",
            "short_summary": str(raw_step),
        }

    step_name = raw_step.get("step_name") or raw_step.get("step") or "execution"
    agent_name = raw_step.get("agent_name") or fallback_agent_name
    status = raw_step.get("status") or "completed"
    short_summary = raw_step.get("short_summary") or raw_step.get("summary")

    normalized = {
        "step_index": raw_step.get("step_index") or raw_step.get("step_number"),
        "step_number": raw_step.get("step_number") or raw_step.get("step_index"),
        "step_name": step_name,
        "agent_name": agent_name,
        "status": status,
        "short_summary": short_summary,
        "result_preview": raw_step.get("result_preview") or short_summary,
        "used_previous_output": bool(raw_step.get("used_previous_output", False)),
        "started_at": raw_step.get("started_at"),
        "finished_at": raw_step.get("finished_at"),
        "duration_ms": raw_step.get("duration_ms"),
        "error_message": raw_step.get("error_message"),
        "llm_provider": raw_step.get("llm_provider"),
        "llm_model": raw_step.get("llm_model"),
        "llm_prompt_tokens": raw_step.get("llm_prompt_tokens"),
        "llm_completion_tokens": raw_step.get("llm_completion_tokens"),
        "llm_total_tokens": raw_step.get("llm_total_tokens"),
        "llm_estimated_cost": raw_step.get("llm_estimated_cost"),
        "llm_fallback_used": raw_step.get("llm_fallback_used"),
        "llm_error": raw_step.get("llm_error"),
        "llm_retry_count": raw_step.get("llm_retry_count"),
        "llm_latency_ms": raw_step.get("llm_latency_ms"),
        "llm_usage_summary": raw_step.get("llm_usage_summary"),
        "rag_enabled": raw_step.get("rag_enabled"),
        "rag_vector_backend": raw_step.get("rag_vector_backend"),
        "rag_context_used": raw_step.get("rag_context_used"),
        "rag_retrieved_chunks_count": raw_step.get("rag_retrieved_chunks_count"),
        "rag_documents_used": raw_step.get("rag_documents_used"),
        "rag_error": raw_step.get("rag_error"),
        "rag_context_chars": raw_step.get("rag_context_chars"),
        "rag_snippets": raw_step.get("rag_snippets"),
        "rag_scores": raw_step.get("rag_scores"),
    }
    return normalized


def _serialize_trace_steps(task: Task) -> list[TaskExecutionStepRead]:
    return [
        TaskExecutionStepRead.model_validate(
            _normalize_trace_step(step, task.agent_name or "GeneralAssistantAgent")
        )
        for step in (task.execution_trace or [])
    ]


def _serialize_task(task: Task, execution: TaskExecutionResult | None = None) -> TaskRead:
    now = datetime.now(UTC)
    payload = {
        "id": task.id,
        "user_id": task.user_id,
        "title": task.title,
        "description": task.description,
        "status": task.status or "pending",
        "task_type": task.task_type or "general",
        "agent_name": task.agent_name or "GeneralAssistantAgent",
        "result_text": task.result_text,
        "execution_trace": _serialize_trace_steps(task),
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "duration_ms": task.duration_ms,
        "executed_at": task.executed_at,
        "error_message": task.error_message,
        "feedback_rating": task.feedback_rating,
        "feedback_comment": task.feedback_comment,
        "feedback_submitted_at": task.feedback_submitted_at,
        "created_at": task.created_at or now,
        "updated_at": task.updated_at or now,
        "rag_debug": None,
    }

    if execution is not None and execution.rag_debug is not None:
        payload["rag_debug"] = TaskRagDebugRead(
            query=execution.rag_debug.query,
            top_k=execution.rag_debug.top_k,
            min_score=execution.rag_debug.min_score,
            retrieved_chunks=[
                TaskRagChunkRead(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    document_title=chunk.document_title,
                    source_name=chunk.source_name,
                    chunk_index=chunk.chunk_index,
                    score=chunk.score,
                    text=chunk.text,
                )
                for chunk in execution.rag_debug.retrieved_chunks
            ],
            memory_task_count=execution.rag_debug.memory_task_count,
            context_preview=execution.rag_debug.context_preview,
            memory_context_preview=execution.rag_debug.memory_context_preview,
            full_context_preview=execution.rag_debug.full_context_preview,
            context_truncated=execution.rag_debug.context_truncated,
            memory_context_truncated=execution.rag_debug.memory_context_truncated,
            full_context_truncated=execution.rag_debug.full_context_truncated,
            retrieval_error=execution.rag_debug.retrieval_error,
        )

    return TaskRead(**payload)


def _get_user_task(
    task_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> Task:
    task = db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task_type = classify_task(
        title=task_in.title,
        description=task_in.description,
    )
    agent_name = select_agent(task_type)

    task = Task(
        id=uuid.uuid4(),
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        task_type=task_type,
        agent_name=agent_name,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return _serialize_task(task)


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    task_status: str | None = Query(default=None, alias="status"),
    task_type: str | None = Query(default=None),
    agent_name: str | None = Query(default=None),
    feedback_rating: int | None = Query(default=None, ge=1, le=5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TaskRead]:
    query = select(Task).where(Task.user_id == current_user.id)

    if task_status:
        query = query.where(Task.status == task_status)

    if task_type:
        query = query.where(Task.task_type == task_type)

    if agent_name:
        query = query.where(Task.agent_name == agent_name)

    if feedback_rating is not None:
        query = query.where(Task.feedback_rating == feedback_rating)

    tasks = db.execute(
        query.order_by(Task.created_at.desc())
    ).scalars().all()

    return [_serialize_task(task) for task in tasks]


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskRead:
    task = _get_user_task(task_id, current_user, db)
    return _serialize_task(task)


@router.get("/tasks/{task_id}/trace", response_model=TaskTraceRead)
def get_task_trace(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskTraceRead:
    task = _get_user_task(task_id, current_user, db)

    return TaskTraceRead(
        task_id=task.id,
        status=task.status,
        started_at=task.started_at,
        finished_at=task.finished_at,
        duration_ms=task.duration_ms,
        execution_trace=_serialize_trace_steps(task),
    )


@router.post("/tasks/{task_id}/execute", response_model=TaskRead)
def execute_user_task(
    task_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    debug: bool = Query(default=False),
    top_k: int | None = Query(default=None, ge=1, le=10),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskRead:
    task = _get_user_task(task_id, current_user, db)

    mode = get_task_execution_mode()

    if mode == "background":
        try:
            queued_task = queue_task_for_background(task, db)
        except TaskExecutionStateError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error

        background_tasks.add_task(
            run_task_execution_background,
            task_id=queued_task.id,
            user_id=current_user.id,
            debug=debug,
            top_k=top_k,
            min_score=min_score,
        )
        return _serialize_task(queued_task)

    try:
        execution = execute_task(
            task,
            db,
            debug=debug,
            top_k=top_k,
            min_score=min_score,
        )
        return _serialize_task(execution.task, execution=execution)
    except TaskExecutionStateError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except TaskExecutionError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


@router.post("/tasks/{task_id}/feedback", response_model=TaskRead)
def submit_task_feedback(
    task_id: uuid.UUID,
    feedback_in: TaskFeedbackUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskRead:
    task = _get_user_task(task_id, current_user, db)
    if task.status not in {"completed", "failed"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task feedback is available only after execution is finished.",
        )

    task.feedback_rating = feedback_in.feedback_rating
    task.feedback_comment = (feedback_in.feedback_comment or "").strip() or None
    task.feedback_submitted_at = datetime.now(UTC)

    db.add(task)
    db.commit()
    db.refresh(task)

    return _serialize_task(task)
