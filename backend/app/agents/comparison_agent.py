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
    title_lower = task.title.lower()
    mentions_fastapi = "fastapi" in title_lower or "fastapi" in description.lower()
    mentions_django = "django" in title_lower or "django" in description.lower()

    subject_a = "FastAPI" if mentions_fastapi else "Option A"
    subject_b = "Django" if mentions_django else "Option B"

    return (
        f"Comparison analysis for: {task.title}\n\n"
        f"Subjects:\n- {subject_a}\n- {subject_b}\n\n"
        "Advantages / Pros:\n"
        f"- {subject_a}: faster iteration and simpler API-focused development.\n"
        f"- {subject_b}: richer built-in features and stronger admin ecosystem.\n\n"
        "Disadvantages / Cons:\n"
        f"- {subject_a}: fewer batteries-included components for large monolith use cases.\n"
        f"- {subject_b}: heavier framework footprint for lightweight API services.\n\n"
        "Recommendation:\n"
        f"- Use {subject_a} for API-first speed and async workloads.\n"
        f"- Use {subject_b} when you need integrated admin and broader built-ins.\n\n"
        f"Notes considered: {description}"
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return generate_text(
        prompt=_build_prompt(task, retrieved_context=retrieved_context),
        fallback_text=_build_fallback(task),
    )
