from app.models.task import Task
from app.agents.prompt_utils import build_retrieved_context_block
from app.services.llm_service import generate_text


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are SummaryAgent inside Aegis, a task execution system.\n"
        "Create a concise and clear summary based on the task input.\n"
        "Prefer short structured output over long prose.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Return a short summary with key points."
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        f"Summary for: {task.title}\n\n"
        "Core points:\n"
        f"- Title: {task.title}\n"
        f"- Context: {description}\n"
        "- Main idea: prioritize the most relevant information first.\n"
        "- Key takeaway: keep implementation focused on practical outcomes.\n"
        "- Recommendation: use this summary as the baseline for next decisions."
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return generate_text(
        prompt=_build_prompt(task, retrieved_context=retrieved_context),
        fallback_text=_build_fallback(task),
    )
