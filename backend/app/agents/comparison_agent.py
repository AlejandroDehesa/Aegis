from app.agents.execution_result import AgentExecutionResult
from app.agents.prompts import build_comparison_fallback, build_comparison_prompt
from app.models.task import Task
from app.services.llm.schemas import LLMRequest
from app.services.llm_service import generate


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    return build_comparison_prompt(
        title=task.title,
        description=task.description or "No additional comparison context provided.",
        retrieved_context=retrieved_context,
    )


def _build_fallback(task: Task, retrieved_context: str | None = None) -> str:
    return build_comparison_fallback(
        title=task.title,
        description=task.description or "No additional comparison context provided.",
        retrieved_context=retrieved_context,
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return run_task_with_metadata(task, retrieved_context=retrieved_context).text


def run_task_with_metadata(task: Task, retrieved_context: str | None = None) -> AgentExecutionResult:
    response = generate(
        request=LLMRequest(prompt=_build_prompt(task, retrieved_context=retrieved_context)),
        fallback_text=_build_fallback(task, retrieved_context=retrieved_context),
    )
    return AgentExecutionResult.from_llm_response(response)
