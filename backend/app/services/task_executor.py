from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.task import Task
from app.services.task_orchestrator import (
    OrchestrationRagDebugInfo,
    TaskOrchestrationError,
    orchestrate_task,
)


TASK_STATUS_PENDING = "pending"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"
EXECUTABLE_TASK_STATUSES = {TASK_STATUS_PENDING, TASK_STATUS_FAILED}


class TaskExecutionError(Exception):
    pass


class TaskExecutionStateError(TaskExecutionError):
    pass


@dataclass
class TaskExecutionResult:
    task: Task
    rag_debug: OrchestrationRagDebugInfo | None = None


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

    task_started_at = _utc_now()
    task.status = TASK_STATUS_PROCESSING
    task.error_message = None
    task.result_text = None
    task.execution_trace = []
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
        task.execution_trace = orchestration_result.execution_trace
        task.status = TASK_STATUS_COMPLETED
        task.error_message = None
        task.finished_at = task_finished_at
        task.executed_at = task_finished_at
        task.duration_ms = _calculate_duration_ms(task.started_at, task.finished_at)
    except TaskOrchestrationError as error:
        task_finished_at = _utc_now()
        task.result_text = None
        task.execution_trace = error.execution_trace
        task.status = TASK_STATUS_FAILED
        task.error_message = str(error)
        task.finished_at = task_finished_at
        task.executed_at = task_finished_at
        task.duration_ms = _calculate_duration_ms(task.started_at, task.finished_at)
        _persist_task(task, db)
        raise TaskExecutionError("Task execution failed.") from error
    except Exception as error:
        task_finished_at = _utc_now()
        task.result_text = None
        task.execution_trace = []
        task.status = TASK_STATUS_FAILED
        task.error_message = str(error)
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
