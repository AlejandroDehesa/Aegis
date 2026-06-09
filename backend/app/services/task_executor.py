from dataclasses import dataclass
from datetime import datetime, timezone
import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.task import Task
from app.services.task_orchestrator import (
    OrchestrationRagDebugInfo,
    TaskOrchestrationError,
    orchestrate_task,
)


TASK_STATUS_PENDING = "pending"
TASK_STATUS_QUEUED = "queued"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"
EXECUTABLE_TASK_STATUSES = {TASK_STATUS_PENDING, TASK_STATUS_FAILED, TASK_STATUS_QUEUED}
VALID_TASK_EXECUTION_MODES = {"sync", "background"}


SECRET_TOKEN_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]+")
BEARER_TOKEN_PATTERN = re.compile(r"(Bearer\s+)[^\s]+", re.IGNORECASE)


class TaskExecutionError(Exception):
    pass


class TaskExecutionStateError(TaskExecutionError):
    pass


@dataclass
class TaskExecutionResult:
    task: Task
    rag_debug: OrchestrationRagDebugInfo | None = None


def _sanitize_error_message(message: str, api_key: str | None = None) -> str:
    sanitized = (message or "").strip()
    sanitized = SECRET_TOKEN_PATTERN.sub("sk-or-***", sanitized)
    sanitized = BEARER_TOKEN_PATTERN.sub(r"\1***", sanitized)
    if api_key:
        sanitized = sanitized.replace(api_key, "sk-or-***")
    return sanitized or "Task execution failed."


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _calculate_duration_ms(
    started_at: datetime | None,
    finished_at: datetime | None,
) -> int | None:
    if started_at is None or finished_at is None:
        return None

    duration = finished_at - started_at
    return max(int(duration.total_seconds() * 1000), 0)


def _persist_task(task: Task, db: Session) -> Task:
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task_execution_mode() -> str:
    mode = (settings.TASK_EXECUTION_MODE or "background").strip().lower()
    if mode not in VALID_TASK_EXECUTION_MODES:
        return "background"
    return mode


def queue_task_for_background(task: Task, db: Session) -> Task:
    if task.status not in {TASK_STATUS_PENDING, TASK_STATUS_FAILED}:
        raise TaskExecutionStateError(
            f"Task cannot be executed from status '{task.status}'."
        )

    now = _utc_now()
    task.status = TASK_STATUS_QUEUED
    task.error_message = None
    task.result_text = None
    task.started_at = None
    task.finished_at = None
    task.duration_ms = None
    task.executed_at = None
    task.execution_trace = [
        {
            "step_name": "queued",
            "agent_name": "TaskExecutor",
            "status": "completed",
            "short_summary": "Task accepted for background execution.",
            "used_previous_output": False,
            "started_at": now.isoformat(),
            "finished_at": now.isoformat(),
            "duration_ms": 0,
        }
    ]
    return _persist_task(task, db)


def _mark_task_failed(
    task: Task,
    db: Session,
    message: str,
) -> None:
    finished_at = _utc_now()
    sanitized_error = _sanitize_error_message(
        message,
        api_key=settings.OPENROUTER_API_KEY,
    )
    trace = list(task.execution_trace or [])
    trace.append(
        {
            "step_name": "execution",
            "agent_name": task.agent_name or "TaskExecutor",
            "status": "failed",
            "short_summary": "Background execution failed before completion.",
            "result_preview": None,
            "used_previous_output": False,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "finished_at": finished_at.isoformat(),
            "duration_ms": _calculate_duration_ms(task.started_at, finished_at),
            "error_message": sanitized_error,
        }
    )
    task.execution_trace = trace
    task.status = TASK_STATUS_FAILED
    task.error_message = sanitized_error
    task.finished_at = finished_at
    task.executed_at = finished_at
    task.duration_ms = _calculate_duration_ms(task.started_at, finished_at)
    _persist_task(task, db)


def execute_task(
    task: Task,
    db: Session,
    *,
    debug: bool = False,
    top_k: int | None = None,
    min_score: float | None = None,
) -> TaskExecutionResult:
    if task.status not in EXECUTABLE_TASK_STATUSES:
        raise TaskExecutionStateError(
            f"Task cannot be executed from status '{task.status}'."
        )

    existing_trace_prefix = list(task.execution_trace or [])
    preserve_queued_prefix = task.status == TASK_STATUS_QUEUED and bool(existing_trace_prefix)

    task_started_at = _utc_now()
    task.status = TASK_STATUS_PROCESSING
    task.error_message = None
    task.result_text = None
    task.execution_trace = existing_trace_prefix if preserve_queued_prefix else []
    task.started_at = task_started_at
    task.finished_at = None
    task.duration_ms = None
    task.executed_at = None
    _persist_task(task, db)

    try:
        orchestration_result = orchestrate_task(
            task,
            db,
            top_k=top_k,
            min_score=min_score,
        )
        task_finished_at = _utc_now()
        task.result_text = orchestration_result.final_output
        task.execution_trace = (
            existing_trace_prefix + orchestration_result.execution_trace
            if preserve_queued_prefix
            else orchestration_result.execution_trace
        )
        task.status = TASK_STATUS_COMPLETED
        task.error_message = None
        task.finished_at = task_finished_at
        task.executed_at = task_finished_at
        task.duration_ms = _calculate_duration_ms(task.started_at, task.finished_at)
    except TaskOrchestrationError as error:
        task_finished_at = _utc_now()
        task.result_text = None
        task.execution_trace = (
            existing_trace_prefix + error.execution_trace
            if preserve_queued_prefix
            else error.execution_trace
        )
        task.status = TASK_STATUS_FAILED
        task.error_message = _sanitize_error_message(
            str(error),
            api_key=settings.OPENROUTER_API_KEY,
        )
        task.finished_at = task_finished_at
        task.executed_at = task_finished_at
        task.duration_ms = _calculate_duration_ms(task.started_at, task.finished_at)
        _persist_task(task, db)
        raise TaskExecutionError("Task execution failed.") from error
    except Exception as error:
        task_finished_at = _utc_now()
        task.result_text = None
        task.execution_trace = existing_trace_prefix if preserve_queued_prefix else []
        task.status = TASK_STATUS_FAILED
        task.error_message = _sanitize_error_message(
            str(error),
            api_key=settings.OPENROUTER_API_KEY,
        )
        task.finished_at = task_finished_at
        task.executed_at = task_finished_at
        task.duration_ms = _calculate_duration_ms(task.started_at, task.finished_at)
        _persist_task(task, db)
        raise TaskExecutionError("Task execution failed.") from error

    persisted_task = _persist_task(task, db)
    return TaskExecutionResult(
        task=persisted_task,
        rag_debug=orchestration_result.rag_debug if debug else None,
    )


def run_task_execution_background(
    task_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    debug: bool = False,
    top_k: int | None = None,
    min_score: float | None = None,
) -> None:
    db = SessionLocal()
    try:
        task = db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.user_id == user_id,
            )
        ).scalar_one_or_none()
        if task is None:
            return

        try:
            execute_task(
                task,
                db,
                debug=debug,
                top_k=top_k,
                min_score=min_score,
            )
        except TaskExecutionStateError as error:
            _mark_task_failed(task, db, str(error))
        except TaskExecutionError:
            # execute_task already persisted failed state and sanitized error.
            return
        except Exception as error:
            _mark_task_failed(task, db, str(error))
    finally:
        db.close()
