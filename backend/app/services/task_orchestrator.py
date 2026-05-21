from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
import unicodedata

from sqlalchemy.orm import Session

from app.agents.analysis_agent import run_task_with_metadata as run_analysis_task
from app.agents.comparison_agent import run_task_with_metadata as run_comparison_task
from app.agents.execution_result import AgentExecutionResult
from app.agents.general_assistant_agent import run_task_with_metadata as run_general_task
from app.agents.planning_agent import run_task_with_metadata as run_planning_task
from app.agents.research_agent import run_task_with_metadata as run_research_task
from app.agents.summary_agent import run_task_with_metadata as run_summary_task
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
    "AnalysisAgent": run_analysis_task,
    "PlanningAgent": run_planning_task,
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
    "analysis": [
        ("analysis", "AnalysisAgent"),
    ],
    "planning": [
        ("planning", "PlanningAgent"),
    ],
    "general": [
        ("general", "GeneralAssistantAgent"),
    ],
}

FORBIDDEN_PLACEHOLDER_PHRASES = (
    "future expansion",
    "ready for future expansion",
    "placeholder",
    "mock response",
    "todo",
    "not implemented",
    "general assistant workflow",
    "processed with the general assistant workflow",
    "dummy",
    "stub",
)
MIN_OUTPUT_LENGTH = 80


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
    enabled: bool = True
    retrieved_chunks_count: int = 0
    documents_used: list[str] = field(default_factory=list)
    empty_reason: str | None = None
    context_chars: int = 0
    trace_snippets: list[str] = field(default_factory=list)
    vector_backend: str = "pgvector"


@dataclass
class RAGContext:
    enabled: bool
    query: str
    retrieved_chunks: list[RetrievedChunk]
    retrieved_chunks_count: int
    documents_used: list[str]
    empty_reason: str | None
    context_text: str | None
    context_chars: int
    snippets: list[str]
    truncated: bool
    vector_backend: str
    error: str | None = None


@dataclass
class FullContextBuildResult:
    text: str | None
    truncated: bool


@dataclass
class TaskOrchestrationResult:
    final_output: str
    execution_trace: list[dict[str, object]]
    rag_debug: OrchestrationRagDebugInfo
    llm_usage_summary: dict[str, object] | None = None


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


def _normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFD", lowered)
        if unicodedata.category(char) != "Mn"
    )
    normalized = re.sub(r"[^a-z0-9\s]", " ", without_accents)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _contains_any_heading_token(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) is not None for pattern in patterns)


def _validate_output_quality(task: Task, output_text: str | None) -> str | None:
    if not output_text or not output_text.strip():
        return "Generated output is empty."

    normalized_output = _normalize_text(output_text)

    if len(normalized_output) < MIN_OUTPUT_LENGTH:
        return "Generated output is too short to be useful."

    for phrase in FORBIDDEN_PLACEHOLDER_PHRASES:
        if phrase in normalized_output:
            return f"Generated output contains disallowed placeholder language: '{phrase}'."

    if task.task_type == "comparison":
        if "recommend" not in normalized_output and "recomend" not in normalized_output:
            return "Comparison output must include a recommendation."

    if task.task_type == "analysis":
        has_risks = _contains_any_heading_token(
            normalized_output,
            (r"\brisk\b", r"\brisks\b", r"\briesgo\b", r"\briesgos\b"),
        )
        has_impact = _contains_any_heading_token(
            normalized_output,
            (r"\bimpact\b", r"\bimpacts\b", r"\bimpacto\b", r"\bimpactos\b"),
        )
        has_mitigation = _contains_any_heading_token(
            normalized_output,
            (r"\bmitigation\b", r"\bmitigations\b", r"\bmitigacion\b", r"\bmitigaciones\b"),
        )
        if not (has_risks and has_impact and has_mitigation):
            return "Analysis output must include risks, impact, and mitigation."

    if task.task_type == "planning":
        if not re.search(r"\b1\b", normalized_output):
            return "Planning output must include numbered steps."

    normalized_input = _normalize_text(f"{task.title} {task.description or ''}")
    tokens = [token for token in normalized_input.split() if len(token) >= 4]
    if tokens and not any(token in normalized_output for token in tokens[:8]):
        return "Generated output does not reference task-specific content."

    return None


def _prepare_combined_context(
    task: Task,
    db: Session,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> tuple[str | None, OrchestrationRagDebugInfo, RAGContext]:
    query = _build_retrieval_query(task)
    effective_top_k = top_k or settings.RAG_TOP_K
    effective_min_score = settings.RAG_MIN_SCORE if min_score is None else min_score

    rag_enabled = bool(getattr(settings, "RAG_ENABLED", True))
    vector_backend = str(getattr(settings, "RAG_VECTOR_BACKEND", "pgvector"))
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
        enabled=rag_enabled,
        retrieved_chunks_count=0,
        documents_used=[],
        empty_reason=None,
        context_chars=0,
        trace_snippets=[],
        vector_backend=vector_backend,
    )

    rag_context = None
    rag_chunks: list[RetrievedChunk] = []
    rag_truncated = False
    rag_empty_reason: str | None = None
    trace_snippets: list[str] = []

    if not rag_enabled:
        rag_empty_reason = "rag_disabled"
    elif not query:
        rag_empty_reason = "empty_query"
    else:
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
            if not rag_chunks:
                rag_empty_reason = "no_results"
        except Exception as error:
            empty_debug.retrieval_error = str(error)
            rag_empty_reason = "retrieval_failed"

    rag_documents_used = sorted({chunk.document_title for chunk in rag_chunks if chunk.document_title})
    snippet_chars = int(getattr(settings, "RAG_TRACE_SNIPPET_CHARS", 300))
    for chunk in rag_chunks[:3]:
        snippet = " ".join(chunk.text.split())
        if len(snippet) > snippet_chars:
            snippet = f"{snippet[:snippet_chars].rstrip()}..."
        trace_snippets.append(snippet)

    memory_result = get_recent_task_context_result(
        db,
        task.user_id,
        current_task_id=task.id,
    )
    full_context_result = build_full_context(
        rag_context,
        memory_result.text,
    )

    rag_context_contract = RAGContext(
        enabled=rag_enabled,
        query=query,
        retrieved_chunks=rag_chunks,
        retrieved_chunks_count=len(rag_chunks),
        documents_used=rag_documents_used,
        empty_reason=rag_empty_reason,
        context_text=rag_context,
        context_chars=len(rag_context or ""),
        snippets=trace_snippets,
        truncated=rag_truncated,
        vector_backend=vector_backend,
        error=empty_debug.retrieval_error,
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
        enabled=rag_enabled,
        retrieved_chunks_count=len(rag_chunks),
        documents_used=rag_documents_used,
        empty_reason=rag_empty_reason,
        context_chars=len(rag_context or ""),
        trace_snippets=trace_snippets,
        vector_backend=vector_backend,
    ), rag_context_contract


def _get_pipeline(task_type: str) -> list[tuple[str, str]]:
    return PIPELINES_BY_TASK_TYPE.get(
        task_type,
        PIPELINES_BY_TASK_TYPE["general"],
    )


def _build_trace_step(
    *,
    step_index: int,
    step_name: str,
    agent_name: str,
    status: str,
    used_previous_output: bool,
    short_summary: str | None,
    error_message: str | None,
    started_at: datetime | None,
    finished_at: datetime | None,
    llm_metadata: dict[str, object] | None = None,
    llm_usage_summary: dict[str, object] | None = None,
    rag_metadata: dict[str, object] | None = None,
) -> dict[str, object]:
    duration_ms = _calculate_duration_ms(started_at, finished_at)
    step = {
        "step_index": step_index,
        "step_number": step_index,
        "step_name": step_name,
        "agent_name": agent_name,
        "status": status,
        "short_summary": short_summary,
        "result_preview": short_summary,
        "used_previous_output": used_previous_output,
        "started_at": started_at.isoformat() if started_at is not None else None,
        "finished_at": finished_at.isoformat() if finished_at is not None else None,
        "duration_ms": duration_ms,
        "error_message": error_message,
    }
    if llm_metadata is not None:
        step["llm_provider"] = llm_metadata.get("provider")
        step["llm_model"] = llm_metadata.get("model")
        step["llm_prompt_tokens"] = llm_metadata.get("prompt_tokens")
        step["llm_completion_tokens"] = llm_metadata.get("completion_tokens")
        step["llm_total_tokens"] = llm_metadata.get("total_tokens")
        step["llm_estimated_cost"] = llm_metadata.get("estimated_cost")
        step["llm_fallback_used"] = llm_metadata.get("fallback_used")
        step["llm_error"] = llm_metadata.get("error")
        step["llm_retry_count"] = llm_metadata.get("retry_count")
        step["llm_latency_ms"] = llm_metadata.get("latency_ms")
    if llm_usage_summary is not None:
        step["llm_usage_summary"] = llm_usage_summary
    if rag_metadata is not None:
        step["rag_vector_backend"] = rag_metadata.get("rag_vector_backend")
        step["rag_enabled"] = rag_metadata.get("rag_enabled")
        step["rag_context_used"] = rag_metadata.get("rag_context_used")
        step["rag_retrieved_chunks_count"] = rag_metadata.get("rag_retrieved_chunks_count")
        step["rag_documents_used"] = rag_metadata.get("rag_documents_used")
        step["rag_error"] = rag_metadata.get("rag_error")
        step["rag_context_chars"] = rag_metadata.get("rag_context_chars")
        step["rag_snippets"] = rag_metadata.get("rag_snippets")
    return step


def _extract_agent_output(step_output: object) -> tuple[str, dict[str, object] | None]:
    if isinstance(step_output, AgentExecutionResult):
        llm_metadata = {
            "provider": step_output.llm_provider,
            "model": step_output.llm_model,
            "prompt_tokens": step_output.prompt_tokens,
            "completion_tokens": step_output.completion_tokens,
            "total_tokens": step_output.total_tokens,
            "estimated_cost": step_output.estimated_cost,
            "fallback_used": step_output.fallback_used,
            "error": step_output.llm_error,
            "retry_count": step_output.llm_retry_count,
            "latency_ms": step_output.llm_latency_ms,
        }
        return step_output.text, llm_metadata

    if isinstance(step_output, str):
        return step_output, None

    return str(step_output), None


def _build_llm_usage_summary(execution_trace: list[dict[str, object]]) -> dict[str, object]:
    prompt_tokens_total = 0
    completion_tokens_total = 0
    total_tokens_total = 0
    estimated_cost_total = 0.0
    estimated_cost_available = False
    providers: set[str] = set()
    models: set[str] = set()
    fallback_used_any = False
    errors_count = 0
    retries_total = 0
    latency_ms_total = 0
    latency_samples = 0

    for step in execution_trace:
        if step.get("step_name") != "execution":
            continue

        provider = step.get("llm_provider")
        if isinstance(provider, str) and provider.strip():
            providers.add(provider.strip())

        model = step.get("llm_model")
        if isinstance(model, str) and model.strip():
            models.add(model.strip())

        prompt_tokens = step.get("llm_prompt_tokens")
        if isinstance(prompt_tokens, int):
            prompt_tokens_total += prompt_tokens

        completion_tokens = step.get("llm_completion_tokens")
        if isinstance(completion_tokens, int):
            completion_tokens_total += completion_tokens

        total_tokens = step.get("llm_total_tokens")
        if isinstance(total_tokens, int):
            total_tokens_total += total_tokens

        estimated_cost = step.get("llm_estimated_cost")
        if isinstance(estimated_cost, (int, float)):
            estimated_cost_total += float(estimated_cost)
            estimated_cost_available = True

        if bool(step.get("llm_fallback_used")):
            fallback_used_any = True

        if step.get("llm_error"):
            errors_count += 1

        retry_count = step.get("llm_retry_count")
        if isinstance(retry_count, int) and retry_count > 0:
            retries_total += retry_count

        latency_ms = step.get("llm_latency_ms")
        if isinstance(latency_ms, int) and latency_ms >= 0:
            latency_ms_total += latency_ms
            latency_samples += 1

    return {
        "total_prompt_tokens": prompt_tokens_total,
        "total_completion_tokens": completion_tokens_total,
        "total_tokens": total_tokens_total,
        "estimated_cost": estimated_cost_total if estimated_cost_available else None,
        "providers_used": sorted(providers),
        "models_used": sorted(models),
        "fallback_used_any": fallback_used_any,
        "llm_errors_count": errors_count,
        "llm_retry_total": retries_total,
        "llm_average_latency_ms": (latency_ms_total // latency_samples) if latency_samples else None,
    }


def orchestrate_task(
    task: Task,
    db: Session,
    *,
    top_k: int | None = None,
    min_score: float | None = None,
) -> TaskOrchestrationResult:
    prepared_context = _prepare_combined_context(
        task,
        db,
        top_k=top_k,
        min_score=min_score,
    )
    if isinstance(prepared_context, tuple) and len(prepared_context) == 2:
        base_context, rag_debug = prepared_context
        rag_context = RAGContext(
            enabled=bool(getattr(settings, "RAG_ENABLED", True)),
            query=_build_retrieval_query(task),
            retrieved_chunks=[],
            retrieved_chunks_count=0,
            documents_used=[],
            empty_reason="compat_no_rag_context",
            context_text=None,
            context_chars=0,
            snippets=[],
            truncated=False,
            vector_backend=str(getattr(settings, "RAG_VECTOR_BACKEND", "pgvector")),
            error=None,
        )
    else:
        base_context, rag_debug, rag_context = prepared_context
    pipeline = _get_pipeline(task.task_type)
    execution_trace: list[dict[str, object]] = []
    previous_output: str | None = None
    step_index = 1
    cumulative_llm_total_tokens = 0

    classification_started = _utc_now()
    classification_finished = _utc_now()
    execution_trace.append(
        _build_trace_step(
            step_index=step_index,
            step_name="classification",
            agent_name="TaskClassifier",
            status="completed",
            used_previous_output=False,
            short_summary=f"Task classified as '{task.task_type}'.",
            error_message=None,
            started_at=classification_started,
            finished_at=classification_finished,
        )
    )
    step_index += 1

    selected_agents = ", ".join(agent_name for _step_name, agent_name in pipeline)
    selection_started = _utc_now()
    selection_finished = _utc_now()
    execution_trace.append(
        _build_trace_step(
            step_index=step_index,
            step_name="agent_selection",
            agent_name=task.agent_name or "AgentSelector",
            status="completed",
            used_previous_output=False,
            short_summary=f"Selected execution pipeline agents: {selected_agents}.",
            error_message=None,
            started_at=selection_started,
            finished_at=selection_finished,
        )
    )
    step_index += 1

    if not rag_context.enabled:
        retrieval_status = "skipped"
        retrieval_summary = "RAG retrieval skipped because RAG is disabled."
    elif rag_context.error:
        retrieval_status = "failed"
        retrieval_summary = "RAG retrieval failed; continuing without document context."
    else:
        retrieval_status = "completed"
        retrieval_summary = (
            "Retrieved "
            f"{rag_context.retrieved_chunks_count} chunks from {len(rag_context.documents_used)} documents."
        )

    retrieval_started = _utc_now()
    retrieval_finished = _utc_now()
    execution_trace.append(
        _build_trace_step(
            step_index=step_index,
            step_name="document_retrieval",
            agent_name="RAGRetriever",
            status=retrieval_status,
            used_previous_output=False,
            short_summary=retrieval_summary,
            error_message=rag_context.error if retrieval_status == "failed" else None,
            started_at=retrieval_started,
            finished_at=retrieval_finished,
            rag_metadata={
                "rag_vector_backend": rag_context.vector_backend,
                "rag_enabled": rag_context.enabled,
                "rag_context_used": bool(rag_context.context_text),
                "rag_retrieved_chunks_count": rag_context.retrieved_chunks_count,
                "rag_documents_used": rag_context.documents_used,
                "rag_error": rag_context.error,
                "rag_context_chars": rag_context.context_chars,
                "rag_snippets": rag_context.snippets,
            },
        )
    )
    step_index += 1

    for logical_step_name, agent_name in pipeline:
        runner = AGENT_RUNNERS.get(agent_name)
        step_started_at = _utc_now()
        used_previous_output = previous_output is not None

        if runner is None:
            step_finished_at = _utc_now()
            execution_trace.append(
                _build_trace_step(
                    step_index=step_index,
                    step_name="execution",
                    agent_name=agent_name,
                    status="failed",
                    used_previous_output=used_previous_output,
                    short_summary=None,
                    error_message=(
                        f"No execution strategy found for the configured agent '{agent_name}'."
                    ),
                    started_at=step_started_at,
                    finished_at=step_finished_at,
                )
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
            raw_step_output = runner(task, retrieved_context=step_context)
            step_output, llm_metadata = _extract_agent_output(raw_step_output)
            step_finished_at = _utc_now()
        except Exception as error:
            step_finished_at = _utc_now()
            execution_trace.append(
                _build_trace_step(
                    step_index=step_index,
                    step_name="execution",
                    agent_name=agent_name,
                    status="failed",
                    used_previous_output=used_previous_output,
                    short_summary=None,
                    error_message=str(error),
                    started_at=step_started_at,
                    finished_at=step_finished_at,
                )
            )
            raise TaskOrchestrationError(
                (
                    f"Task orchestration failed at step '{logical_step_name}' "
                    f"with agent '{agent_name}': {error}"
                ),
                execution_trace=execution_trace,
                rag_debug=rag_debug,
            ) from error

        output_preview = _build_output_preview(step_output)
        short_summary = (
            f"[{logical_step_name}] {output_preview}"
            if output_preview is not None
            else f"[{logical_step_name}]"
        )
        execution_trace.append(
            _build_trace_step(
                step_index=step_index,
                step_name="execution",
                agent_name=agent_name,
                status="completed",
                used_previous_output=used_previous_output,
                short_summary=short_summary,
                error_message=None,
                started_at=step_started_at,
                finished_at=step_finished_at,
                llm_metadata=llm_metadata,
                rag_metadata={
                    "rag_vector_backend": rag_context.vector_backend,
                    "rag_enabled": rag_context.enabled,
                    "rag_context_used": bool(rag_context.context_text),
                    "rag_retrieved_chunks_count": rag_context.retrieved_chunks_count,
                    "rag_documents_used": rag_context.documents_used,
                    "rag_error": rag_context.error,
                    "rag_context_chars": rag_context.context_chars,
                    "rag_snippets": None,
                },
            )
        )
        if llm_metadata is not None:
            step_tokens = llm_metadata.get("total_tokens")
            if isinstance(step_tokens, int):
                cumulative_llm_total_tokens += step_tokens
                hard_limit = int(getattr(settings, "LLM_TASK_TOTAL_TOKEN_HARD_LIMIT", 10000))
                if hard_limit > 0 and cumulative_llm_total_tokens > hard_limit:
                    step_index += 1
                    failed_started_at = _utc_now()
                    failed_finished_at = _utc_now()
                    execution_trace.append(
                        _build_trace_step(
                            step_index=step_index,
                            step_name="execution",
                            agent_name=agent_name,
                            status="failed",
                            used_previous_output=True,
                            short_summary=None,
                            error_message=(
                                "Task exceeded LLM_TASK_TOTAL_TOKEN_HARD_LIMIT "
                                f"({cumulative_llm_total_tokens} > {hard_limit})."
                            ),
                            started_at=failed_started_at,
                            finished_at=failed_finished_at,
                        )
                    )
                    raise TaskOrchestrationError(
                        "Task orchestration exceeded hard LLM token limit.",
                        execution_trace=execution_trace,
                        rag_debug=rag_debug,
                    )
        step_index += 1
        previous_output = step_output

    quality_error = _validate_output_quality(task, previous_output)
    if quality_error is not None:
        failed_started_at = _utc_now()
        failed_finished_at = _utc_now()
        execution_trace.append(
            _build_trace_step(
                step_index=step_index,
                step_name="execution",
                agent_name=task.agent_name or "UnknownAgent",
                status="failed",
                used_previous_output=previous_output is not None,
                short_summary=None,
                error_message=quality_error,
                started_at=failed_started_at,
                finished_at=failed_finished_at,
            )
        )
        raise TaskOrchestrationError(
            "Generated output did not pass minimum quality checks.",
            execution_trace=execution_trace,
            rag_debug=rag_debug,
        )

    llm_usage_summary = _build_llm_usage_summary(execution_trace)
    soft_limit = int(getattr(settings, "LLM_TASK_TOTAL_TOKEN_SOFT_LIMIT", 6000))
    hard_limit = int(getattr(settings, "LLM_TASK_TOTAL_TOKEN_HARD_LIMIT", 10000))
    llm_usage_summary["soft_limit"] = soft_limit
    llm_usage_summary["hard_limit"] = hard_limit
    llm_usage_summary["soft_limit_exceeded"] = (
        soft_limit > 0 and llm_usage_summary["total_tokens"] > soft_limit
    )
    llm_usage_summary["hard_limit_exceeded"] = (
        hard_limit > 0 and llm_usage_summary["total_tokens"] > hard_limit
    )

    summary_started_at = _utc_now()
    summary_finished_at = _utc_now()
    execution_trace.append(
        _build_trace_step(
            step_index=step_index,
            step_name="llm_usage_summary",
            agent_name="LLMService",
            status="completed",
            used_previous_output=False,
            short_summary=(
                "LLM usage summary: "
                f"total_tokens={llm_usage_summary['total_tokens']}, "
                f"providers={','.join(llm_usage_summary['providers_used']) or 'none'}."
            ),
            error_message=None,
            started_at=summary_started_at,
            finished_at=summary_finished_at,
            llm_usage_summary=llm_usage_summary,
        )
    )

    return TaskOrchestrationResult(
        final_output=previous_output or "",
        execution_trace=execution_trace,
        rag_debug=rag_debug,
        llm_usage_summary=llm_usage_summary,
    )
