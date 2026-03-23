from app.models.task import Task
from app.agents.prompt_utils import build_retrieved_context_block
from app.services.llm_service import generate_text


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional comparison context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are ComparisonAgent inside Aegis, a task execution system.\n"
        "Produce a brief, structured comparison.\n"
        "Keep the output practical and easy to scan.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Return:\n"
        "- Comparison criteria\n"
        "- Main differences\n"
        "- Short recommendation"
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional comparison context provided."

    return (
        f"Comparison analysis for: {task.title}\n\n"
        "Comparison frame:\n"
        f"- Subject: {task.title}\n"
        f"- Notes: {description}\n\n"
        "Structured output:\n"
        "- Item A: requires evaluation.\n"
        "- Item B: requires evaluation.\n"
        "- Final recommendation can be expanded in future execution phases."
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return generate_text(
        prompt=_build_prompt(task, retrieved_context=retrieved_context),
        fallback_text=_build_fallback(task),
    )
