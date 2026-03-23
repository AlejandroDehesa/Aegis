import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRagChunkRead, TaskRagDebugRead, TaskRead
from app.services.agent_selector import select_agent
from app.services.task_classifier import classify_task
from app.services.task_executor import (
    TaskExecutionError,
    TaskExecutionResult,
    TaskExecutionStateError,
    execute_task,
)


router = APIRouter()


def _serialize_task(task: Task, execution: TaskExecutionResult | None = None) -> TaskRead:
    payload = TaskRead.model_validate(task).model_dump()

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
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        task_type=task_type,
        agent_name=agent_name,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Task]:
    tasks = db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
    ).scalars().all()

    return tasks


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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


@router.post("/tasks/{task_id}/execute", response_model=TaskRead)
def execute_user_task(
    task_id: uuid.UUID,
    debug: bool = Query(default=False),
    top_k: int | None = Query(default=None, ge=1, le=10),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TaskRead:
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
