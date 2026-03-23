from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.general_assistant_agent import run_task as run_general_task
from app.agents.research_agent import run_task as run_research_task
from app.agents.summary_agent import run_task as run_summary_task
from app.core.config import settings
from app.models.task import Task
from app.services.memory_service import get_recent_task_context_result
from app.services.retrieval_service import RetrievedChunk, build_context, retrieve_relevant_chunks


MAX_TRACE_PREVIEW_CHARS = 200
MAX_PREVIOUS_OUTPUT_CONTEXT_CHARS = 1200
FULL_CONTEXT_START_DELIMITER = "=== FULL EXECUTION CONTEXT START ==="
FULL_CONTEXT_END_DELIMITER = "=== FULL EXECUTION CONTEXT END ==="
FULL_CONTEXT_SECTION_DELIMITER = "\n\n====\n\n"


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
    memory_task_count: int
    context_preview: str | None
    memory_context_preview: str | None
    full_context_preview: str | None
    context_truncated: bool
    memory_context_truncated: bool
    full_context_truncated: bool
    retrieval_error: str | None = None


@dataclass
class FullContextBuildResult:
    text: str | None
    truncated: bool


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


def _truncate_full_context_block(label: str, text: str, available_chars: int) -> str | None:
    header = f"[{label}]\n"
    ellipsis = "\n..."

    if available_chars <= len(header) + len(ellipsis) + 40:
        return None

    remaining_chars = available_chars - len(header) - len(ellipsis)
    truncated_text = text[:remaining_chars].rstrip()

    if not truncated_text:
        return None

    return f"{header}{truncated_text}{ellipsis}"


def build_full_context(
    rag_context: str | None,
    memory_context: str | None,
    *,
    max_chars: int | None = None,
) -> FullContextBuildResult:
    sections_to_include = []

    if rag_context:
        sections_to_include.append(("RAG CONTEXT", rag_context))

    if memory_context:
        sections_to_include.append(("MEMORY CONTEXT", memory_context))

    if not sections_to_include:
        return FullContextBuildResult(text=None, truncated=False)

    max_full_context_chars = max_chars or settings.FULL_CONTEXT_MAX_CHARS
    sections: list[str] = []
    current_length = len(FULL_CONTEXT_START_DELIMITER) + len(FULL_CONTEXT_END_DELIMITER) + 2
    truncated = False

    for label, text in sections_to_include:
        section = f"[{label}]\n{text}"
        separator_length = len(FULL_CONTEXT_SECTION_DELIMITER) if sections else 0
        projected_length = current_length + separator_length + len(section)

        if projected_length <= max_full_context_chars:
            if sections:
                current_length += len(FULL_CONTEXT_SECTION_DELIMITER)
            sections.append(section)
            current_length += len(section)
            continue

        remaining_chars = max_full_context_chars - current_length - separator_length
        truncated_section = _truncate_full_context_block(label, text, remaining_chars)

        if truncated_section:
            if sections:
                current_length += len(FULL_CONTEXT_SECTION_DELIMITER)
            sections.append(truncated_section)
            current_length += len(truncated_section)

        truncated = True
        break

    if not sections:
        return FullContextBuildResult(text=None, truncated=truncated)

    context_body = FULL_CONTEXT_SECTION_DELIMITER.join(sections)
    return FullContextBuildResult(
        text=f"{FULL_CONTEXT_START_DELIMITER}\n{context_body}\n{FULL_CONTEXT_END_DELIMITER}",
        truncated=truncated,
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


def _prepare_combined_context(
    task: Task,
    db: Session,
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
        memory_task_count=0,
        context_preview=None,
        memory_context_preview=None,
        full_context_preview=None,
        context_truncated=False,
        memory_context_truncated=False,
        full_context_truncated=False,
        retrieval_error=None,
    )

    rag_context = None
    rag_chunks: list[RetrievedChunk] = []
    rag_truncated = False

    if query:
        try:
            rag_chunks = retrieve_relevant_chunks(
                query=query,
                user_id=task.user_id,
                top_k=effective_top_k,
                min_score=effective_min_score,
            )
            rag_result = build_context(rag_chunks)
            rag_context = rag_result.text
            rag_chunks = rag_result.used_chunks
            rag_truncated = rag_result.truncated
        except Exception as error:
            empty_debug.retrieval_error = str(error)

    memory_result = get_recent_task_context_result(
        db,
        task.user_id,
        current_task_id=task.id,
    )
    full_context_result = build_full_context(
        rag_context,
        memory_result.text,
    )

    return full_context_result.text, OrchestrationRagDebugInfo(
        query=query,
        top_k=effective_top_k,
        min_score=effective_min_score,
        retrieved_chunks=rag_chunks,
        memory_task_count=memory_result.task_count,
        context_preview=rag_context,
        memory_context_preview=memory_result.text,
        full_context_preview=full_context_result.text,
        context_truncated=rag_truncated,
        memory_context_truncated=memory_result.truncated,
        full_context_truncated=full_context_result.truncated,
        retrieval_error=empty_debug.retrieval_error,
    )


def _get_pipeline(task_type: str) -> list[tuple[str, str]]:
    return PIPELINES_BY_TASK_TYPE.get(
        task_type,
        PIPELINES_BY_TASK_TYPE["general"],
    )


def orchestrate_task(
    task: Task,
    db: Session,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> TaskOrchestrationResult:
    base_context, rag_debug = _prepare_combined_context(
        task,
        db,
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
