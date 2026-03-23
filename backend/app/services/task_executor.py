from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.general_assistant_agent import run_task as run_general_task
from app.agents.research_agent import run_task as run_research_task
from app.agents.summary_agent import run_task as run_summary_task
from app.core.config import settings
from app.models.task import Task
from app.services.retrieval_service import RetrievedChunk, build_context, retrieve_relevant_chunks


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


@dataclass
class TaskExecutionDebugInfo:
    query: str
    top_k: int
    min_score: float
    retrieved_chunks: list[RetrievedChunk]
    context_preview: str | None
    context_truncated: bool
    retrieval_error: str | None = None


@dataclass
class TaskExecutionResult:
    task: Task
    rag_debug: TaskExecutionDebugInfo | None = None


def _persist_task(task: Task, db: Session) -> Task:
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _build_retrieval_query(task: Task) -> str:
    return (task.description or "").strip() or task.title.strip()


def _prepare_rag_context(
    task: Task,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> tuple[str | None, TaskExecutionDebugInfo]:
    query = _build_retrieval_query(task)
    effective_top_k = top_k or settings.RAG_TOP_K
    effective_min_score = settings.RAG_MIN_SCORE if min_score is None else min_score

    empty_debug = TaskExecutionDebugInfo(
        query=query,
        top_k=effective_top_k,
        min_score=effective_min_score,
        retrieved_chunks=[],
        context_preview=None,
        context_truncated=False,
        retrieval_error=None,
    )

    if not query:
        return None, empty_debug

    try:
        chunks = retrieve_relevant_chunks(
            query=query,
            user_id=task.user_id,
            top_k=effective_top_k,
            min_score=effective_min_score,
        )
        context_result = build_context(chunks)
    except Exception as error:
        empty_debug.retrieval_error = str(error)
        return None, empty_debug

    return context_result.text, TaskExecutionDebugInfo(
        query=query,
        top_k=effective_top_k,
        min_score=effective_min_score,
        retrieved_chunks=context_result.used_chunks,
        context_preview=context_result.text,
        context_truncated=context_result.truncated,
        retrieval_error=None,
    )


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
        retrieved_context, rag_debug = _prepare_rag_context(
            task,
            top_k=top_k,
            min_score=min_score,
        )
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

    persisted_task = _persist_task(task, db)
    return TaskExecutionResult(
        task=persisted_task,
        rag_debug=rag_debug if debug else None,
    )
