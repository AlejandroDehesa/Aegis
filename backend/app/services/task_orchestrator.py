from dataclasses import dataclass

from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.general_assistant_agent import run_task as run_general_task
from app.agents.research_agent import run_task as run_research_task
from app.agents.summary_agent import run_task as run_summary_task
from app.core.config import settings
from app.models.task import Task
from app.services.retrieval_service import RetrievedChunk, build_context, retrieve_relevant_chunks


MAX_TRACE_PREVIEW_CHARS = 200
MAX_PREVIOUS_OUTPUT_CONTEXT_CHARS = 1200


AGENT_RUNNERS = {
    "ResearchAgent": run_research_task,
    "SummaryAgent": run_summary_task,
    "ComparisonAgent": run_comparison_task,
    "GeneralAssistantAgent": run_general_task,
}


PIPELINES_BY_TASK_TYPE = {
    "research": [
        ("research", "ResearchAgent"),
        ("summary", "SummaryAgent"),
    ],
    "comparison": [
        ("research", "ResearchAgent"),
        ("comparison", "ComparisonAgent"),
    ],
    "summary": [
        ("summary", "SummaryAgent"),
    ],
    "general": [
        ("general", "GeneralAssistantAgent"),
    ],
}


@dataclass
class OrchestrationRagDebugInfo:
    query: str
    top_k: int
    min_score: float
    retrieved_chunks: list[RetrievedChunk]
    context_preview: str | None
    context_truncated: bool
    retrieval_error: str | None = None


@dataclass
class TaskOrchestrationResult:
    final_output: str
    execution_trace: list[dict[str, object]]
    rag_debug: OrchestrationRagDebugInfo


class TaskOrchestrationError(Exception):
    def __init__(
        self,
        message: str,
        *,
        execution_trace: list[dict[str, object]],
        rag_debug: OrchestrationRagDebugInfo,
    ) -> None:
        super().__init__(message)
        self.execution_trace = execution_trace
        self.rag_debug = rag_debug


def _build_retrieval_query(task: Task) -> str:
    return (task.description or "").strip() or task.title.strip()


def _build_output_preview(output_text: str | None) -> str | None:
    if not output_text:
        return None

    normalized_text = " ".join(output_text.split())

    if len(normalized_text) <= MAX_TRACE_PREVIEW_CHARS:
        return normalized_text

    return f"{normalized_text[:MAX_TRACE_PREVIEW_CHARS].rstrip()}..."


def _build_previous_output_block(previous_output: str | None) -> str | None:
    if not previous_output:
        return None

    clipped_output = previous_output[:MAX_PREVIOUS_OUTPUT_CONTEXT_CHARS].rstrip()

    if len(previous_output) > MAX_PREVIOUS_OUTPUT_CONTEXT_CHARS:
        clipped_output = f"{clipped_output}\n..."

    return (
        "=== PREVIOUS STEP OUTPUT START ===\n"
        f"{clipped_output}\n"
        "=== PREVIOUS STEP OUTPUT END ==="
    )


def _build_step_context(
    *,
    base_context: str | None,
    previous_output: str | None,
) -> str | None:
    context_sections = []

    if base_context:
        context_sections.append(base_context)

    previous_output_block = _build_previous_output_block(previous_output)
    if previous_output_block:
        context_sections.append(previous_output_block)

    if not context_sections:
        return None

    return "\n\n".join(context_sections)


def _prepare_rag_context(
    task: Task,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> tuple[str | None, OrchestrationRagDebugInfo]:
    query = _build_retrieval_query(task)
    effective_top_k = top_k or settings.RAG_TOP_K
    effective_min_score = settings.RAG_MIN_SCORE if min_score is None else min_score

    empty_debug = OrchestrationRagDebugInfo(
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

    return context_result.text, OrchestrationRagDebugInfo(
        query=query,
        top_k=effective_top_k,
        min_score=effective_min_score,
        retrieved_chunks=context_result.used_chunks,
        context_preview=context_result.text,
        context_truncated=context_result.truncated,
        retrieval_error=None,
    )


def _get_pipeline(task_type: str) -> list[tuple[str, str]]:
    return PIPELINES_BY_TASK_TYPE.get(
        task_type,
        PIPELINES_BY_TASK_TYPE["general"],
    )


def orchestrate_task(
    task: Task,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> TaskOrchestrationResult:
    base_context, rag_debug = _prepare_rag_context(
        task,
        top_k=top_k,
        min_score=min_score,
    )
    pipeline = _get_pipeline(task.task_type)
    execution_trace: list[dict[str, object]] = []
    previous_output: str | None = None

    for step_number, (step_name, agent_name) in enumerate(pipeline, start=1):
        runner = AGENT_RUNNERS.get(agent_name)

        if runner is None:
            execution_trace.append(
                {
                    "step_number": step_number,
                    "step_name": step_name,
                    "agent_name": agent_name,
                    "status": "failed",
                    "used_previous_output": previous_output is not None,
                    "result_preview": None,
                    "error_message": "No execution strategy found for the configured agent.",
                }
            )
            raise TaskOrchestrationError(
                f"No execution strategy found for agent '{agent_name}'.",
                execution_trace=execution_trace,
                rag_debug=rag_debug,
            )

        step_context = _build_step_context(
            base_context=base_context,
            previous_output=previous_output,
        )

        try:
            step_output = runner(task, retrieved_context=step_context)
        except Exception as error:
            execution_trace.append(
                {
                    "step_number": step_number,
                    "step_name": step_name,
                    "agent_name": agent_name,
                    "status": "failed",
                    "used_previous_output": previous_output is not None,
                    "result_preview": None,
                    "error_message": str(error),
                }
            )
            raise TaskOrchestrationError(
                (
                    f"Task orchestration failed at step '{step_name}' "
                    f"with agent '{agent_name}': {error}"
                ),
                execution_trace=execution_trace,
                rag_debug=rag_debug,
            ) from error

        execution_trace.append(
            {
                "step_number": step_number,
                "step_name": step_name,
                "agent_name": agent_name,
                "status": "completed",
                "used_previous_output": previous_output is not None,
                "result_preview": _build_output_preview(step_output),
                "error_message": None,
            }
        )
        previous_output = step_output

    return TaskOrchestrationResult(
        final_output=previous_output or "",
        execution_trace=execution_trace,
        rag_debug=rag_debug,
    )
