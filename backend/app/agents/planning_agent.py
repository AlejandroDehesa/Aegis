from app.agents.execution_result import AgentExecutionResult
from app.agents.prompt_utils import build_retrieved_context_block
from app.models.task import Task
from app.services.llm.schemas import LLMRequest
from app.services.llm_service import generate


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional planning context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are PlanningAgent inside Aegis.\n"
        "Create a practical implementation plan that can be executed incrementally.\n"
        "Make the plan specific to the task and avoid placeholders.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Output format (use these exact section headings):\n"
        "1. Objective\n"
        "2. Phases\n"
        "3. Step-by-step plan\n"
        "4. Dependencies\n"
        "5. Risks\n"
        "6. Next action"
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional planning context provided."

    return (
        "Objective:\n"
        f"- Deliver a reliable implementation for: {task.title}\n\n"
        "Phases:\n"
        "1. Scope definition and architecture alignment.\n"
        "2. Incremental implementation and integration.\n"
        "3. Validation, stabilization, and release readiness.\n\n"
        "Step-by-step plan:\n"
        "1. Define scope and acceptance criteria.\n"
        "2. Split work into backend, integration, and validation tasks.\n"
        "3. Implement smallest end-to-end vertical slice first.\n"
        "4. Add automated checks for each critical behavior.\n"
        "5. Run demo rehearsal and adjust based on results.\n\n"
        "Dependencies:\n"
        "- Stable test environment and reproducible seed data.\n"
        "- Agreement on contracts between services and agents.\n\n"
        "Risks:\n"
        "- Scope growth without explicit acceptance criteria.\n"
        "- Integration regressions if validation is delayed.\n\n"
        f"Context considered: {description}\n\n"
        "Next action:\n"
        "- Start with a short technical spec and a checklist of critical tests."
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return run_task_with_metadata(task, retrieved_context=retrieved_context).text


def run_task_with_metadata(task: Task, retrieved_context: str | None = None) -> AgentExecutionResult:
    response = generate(
        request=LLMRequest(prompt=_build_prompt(task, retrieved_context=retrieved_context)),
        fallback_text=_build_fallback(task),
    )
    return AgentExecutionResult.from_llm_response(response)
