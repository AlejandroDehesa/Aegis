from app.models.task import Task
from app.agents.prompt_utils import build_retrieved_context_block
from app.services.llm_service import generate_text


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are GeneralAssistantAgent inside Aegis, a task execution system.\n"
        "Provide a useful, direct response to the task.\n"
        "Keep the result clear, practical, and concise.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Return a helpful response and a short suggested next step."
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        f"Response for: {task.title}\n\n"
        f"Request summary:\n- {task.title}\n"
        f"- {description}\n\n"
        "Recommended approach:\n"
        "1. Clarify the exact scope and expected output format.\n"
        "2. Break the task into small actionable steps.\n"
        "3. Execute the highest-impact step first and validate results.\n\n"
        "Next step:\n"
        "- Start with a concise outline and confirm success criteria."
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return generate_text(
        prompt=_build_prompt(task, retrieved_context=retrieved_context),
        fallback_text=_build_fallback(task),
    )
