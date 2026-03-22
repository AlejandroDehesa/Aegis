from app.models.task import Task
from app.services.llm_service import generate_text


def _build_prompt(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        "You are GeneralAssistantAgent inside Aegis, a task execution system.\n"
        "Provide a useful, direct response to the task.\n"
        "Keep the result clear, practical, and concise.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        "Return a helpful response and a short suggested next step."
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        f"General assistance output for: {task.title}\n\n"
        f"Request:\n- {task.title}\n"
        f"Context:\n- {description}\n\n"
        "Suggested next step:\n"
        "- The task has been processed with the general assistant workflow.\n"
        "- It is ready for future expansion with richer agent capabilities."
    )


def run_task(task: Task) -> str:
    return generate_text(
        prompt=_build_prompt(task),
        fallback_text=_build_fallback(task),
    )
