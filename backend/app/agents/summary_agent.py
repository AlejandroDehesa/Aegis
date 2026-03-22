from app.models.task import Task
from app.services.llm_service import generate_text


def _build_prompt(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        "You are SummaryAgent inside Aegis, a task execution system.\n"
        "Create a concise and clear summary based on the task input.\n"
        "Prefer short structured output over long prose.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        "Return a short summary with key points."
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        f"Summary for: {task.title}\n\n"
        "Core points:\n"
        f"- Title: {task.title}\n"
        f"- Context: {description}\n"
        "- A concise synthesis has been prepared.\n"
        "- This task fits a summary-oriented workflow."
    )


def run_task(task: Task) -> str:
    return generate_text(
        prompt=_build_prompt(task),
        fallback_text=_build_fallback(task),
    )
