from app.agents.execution_result import AgentExecutionResult
from app.models.task import Task
from app.agents.prompt_utils import build_retrieved_context_block
from app.services.llm.schemas import LLMRequest
from app.services.llm_service import generate


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are ResearchAgent inside Aegis, a task execution system.\n"
        "Produce a brief, structured research-style response.\n"
        "Keep the answer practical and easy to scan.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Return:\n"
        "1. Research goal\n"
        "2. Key observations\n"
        "3. Suggested next step"
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        f"Research overview for: {task.title}\n\n"
        f"Objective:\n- {task.title}\n\n"
        f"Context:\n- {description}\n\n"
        "Initial findings:\n"
        "- Key topics have been identified for further investigation.\n"
        "- Priority options were identified based on likely impact.\n"
        "- Recommendation: validate assumptions with concrete source checks next."
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return run_task_with_metadata(task, retrieved_context=retrieved_context).text


def run_task_with_metadata(task: Task, retrieved_context: str | None = None) -> AgentExecutionResult:
    response = generate(
        request=LLMRequest(prompt=_build_prompt(task, retrieved_context=retrieved_context)),
        fallback_text=_build_fallback(task),
    )
    return AgentExecutionResult.from_llm_response(response)
