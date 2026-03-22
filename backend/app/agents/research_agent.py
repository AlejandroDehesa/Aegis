from app.models.task import Task
from app.services.llm_service import generate_text


def _build_prompt(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        "You are ResearchAgent inside Aegis, a task execution system.\n"
        "Produce a brief, structured research-style response.\n"
        "Keep the answer practical and easy to scan.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
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
        "- A deeper source-by-source analysis can be executed in a future phase.\n"
        "- This task is suitable for a research-oriented workflow."
    )


def run_task(task: Task) -> str:
    return generate_text(
        prompt=_build_prompt(task),
        fallback_text=_build_fallback(task),
    )
