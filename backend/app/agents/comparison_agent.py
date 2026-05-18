from app.agents.execution_result import AgentExecutionResult
from app.models.task import Task
from app.agents.prompt_utils import build_retrieved_context_block
from app.services.llm.schemas import LLMRequest
from app.services.llm_service import generate


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional comparison context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are ComparisonAgent inside Aegis.\n"
        "Provide an executive-level comparison that is practical and task-specific.\n"
        "Avoid placeholder language and generic statements.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Output format (use these exact section headings):\n"
        "1. Executive summary\n"
        "2. Compared options\n"
        "3. Advantages / Pros\n"
        "4. Disadvantages / Cons\n"
        "5. Best use cases\n"
        "6. Final recommendation\n"
        "7. Assumptions / caveats (if applicable)"
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional comparison context provided."
    title_lower = task.title.lower()
    mentions_fastapi = "fastapi" in title_lower or "fastapi" in description.lower()
    mentions_django = "django" in title_lower or "django" in description.lower()

    subject_a = "FastAPI" if mentions_fastapi else "Option A"
    subject_b = "Django" if mentions_django else "Option B"

    return (
        "Executive summary:\n"
        f"- This comparison evaluates {subject_a} and {subject_b} for the requested task.\n\n"
        "Compared options:\n"
        f"- Option A: {subject_a}\n"
        f"- Option B: {subject_b}\n\n"
        "Advantages / Pros:\n"
        f"- {subject_a}: faster iteration and simpler API-focused development.\n"
        f"- {subject_b}: richer built-in features and stronger admin ecosystem.\n\n"
        "Disadvantages / Cons:\n"
        f"- {subject_a}: fewer batteries-included components for large monolith use cases.\n"
        f"- {subject_b}: heavier framework footprint for lightweight API services.\n\n"
        "Best use cases:\n"
        f"- {subject_a}: API-first products, async-heavy workloads, rapid prototyping.\n"
        f"- {subject_b}: admin-centric platforms, content-heavy backoffice workflows.\n\n"
        "Final recommendation:\n"
        f"- Use {subject_a} for API-first speed and async workloads.\n"
        f"- Use {subject_b} when you need integrated admin and broader built-ins.\n\n"
        "Assumptions / caveats:\n"
        f"- Recommendation assumes current context: {description}"
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return run_task_with_metadata(task, retrieved_context=retrieved_context).text


def run_task_with_metadata(task: Task, retrieved_context: str | None = None) -> AgentExecutionResult:
    response = generate(
        request=LLMRequest(prompt=_build_prompt(task, retrieved_context=retrieved_context)),
        fallback_text=_build_fallback(task),
    )
    return AgentExecutionResult.from_llm_response(response)
