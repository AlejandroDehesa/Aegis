from app.agents.prompt_utils import build_retrieved_context_block
from app.models.task import Task
from app.services.llm_service import generate_text


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional planning context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are PlanningAgent inside Aegis.\n"
        "Create a practical and ordered implementation plan.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Return:\n"
        "1. Numbered steps in order\n"
        "2. Objective of each step\n"
        "3. Immediate next action"
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional planning context provided."

    return (
        f"Implementation plan for: {task.title}\n\n"
        "1. Define scope and acceptance criteria.\n"
        "2. Split work into backend, integration, and validation tasks.\n"
        "3. Implement smallest end-to-end vertical slice first.\n"
        "4. Add automated checks for each critical behavior.\n"
        "5. Run demo rehearsal and adjust based on results.\n\n"
        f"Context considered: {description}\n\n"
        "Next action:\n"
        "- Start with a short technical spec and a checklist of critical tests."
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return generate_text(
        prompt=_build_prompt(task, retrieved_context=retrieved_context),
        fallback_text=_build_fallback(task),
    )
