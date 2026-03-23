from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.general_assistant_agent import run_task as run_general_task
from app.agents.research_agent import run_task as run_research_task
from app.agents.summary_agent import run_task as run_summary_task
from app.models.task import Task
from app.services.retrieval_service import (
    format_retrieved_context,
    retrieve_relevant_chunks,
)


TASK_STATUS_PENDING = "pending"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"
EXECUTABLE_TASK_STATUSES = {TASK_STATUS_PENDING, TASK_STATUS_FAILED}


AGENT_RUNNERS = {
    "ResearchAgent": run_research_task,
    "SummaryAgent": run_summary_task,
    "ComparisonAgent": run_comparison_task,
    "GeneralAssistantAgent": run_general_task,
}


class TaskExecutionError(Exception):
    pass


class TaskExecutionStateError(TaskExecutionError):
    pass


def _persist_task(task: Task, db: Session) -> Task:
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _build_retrieved_context(task: Task) -> str | None:
    query = (task.description or "").strip() or task.title.strip()

    if not query:
        return None

    try:
        chunks = retrieve_relevant_chunks(
            query=query,
            user_id=task.user_id,
        )
    except Exception:
        return None

    return format_retrieved_context(chunks)


def execute_task(task: Task, db: Session) -> Task:
    if task.status not in EXECUTABLE_TASK_STATUSES:
        raise TaskExecutionStateError(
            f"Task cannot be executed from status '{task.status}'."
        )

    runner = AGENT_RUNNERS.get(task.agent_name)

    if runner is None:
        task.status = TASK_STATUS_FAILED
        task.result_text = None
        task.error_message = "No execution strategy found for the selected agent."
        task.executed_at = None
        _persist_task(task, db)
        raise TaskExecutionError("No execution strategy found for the selected agent.")

    task.status = TASK_STATUS_PROCESSING
    task.error_message = None
    _persist_task(task, db)

    try:
        retrieved_context = _build_retrieved_context(task)
        result_text = runner(task, retrieved_context=retrieved_context)
        task.result_text = result_text
        task.status = TASK_STATUS_COMPLETED
        task.error_message = None
        task.executed_at = datetime.now(timezone.utc)
    except Exception as error:
        task.result_text = None
        task.status = TASK_STATUS_FAILED
        task.error_message = str(error)
        task.executed_at = None
        _persist_task(task, db)
        raise TaskExecutionError("Task execution failed.") from error

    return _persist_task(task, db)
