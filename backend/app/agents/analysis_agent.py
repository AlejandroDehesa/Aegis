from app.agents.prompt_utils import build_retrieved_context_block
from app.models.task import Task
from app.services.llm_service import generate_text


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional analysis context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are AnalysisAgent inside Aegis.\n"
        "Deliver a practical risk analysis with clear structure.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Return:\n"
        "1. Main risks\n"
        "2. Impact per risk\n"
        "3. Mitigation per risk\n"
        "4. Short recommendation"
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional analysis context provided."

    return (
        f"Risk analysis for: {task.title}\n\n"
        "Risks:\n"
        "- Risk 1: Deployment instability due to environment misconfiguration.\n"
        "- Risk 2: Service interruption under load spikes.\n\n"
        "Impact:\n"
        "- Delays in delivery and degraded user experience.\n\n"
        "Mitigation:\n"
        "- Use staged rollout, health checks, and rollback plan.\n"
        "- Add monitoring and capacity alerts before release.\n\n"
        f"Context considered: {description}\n\n"
        "Recommendation:\n"
        "- Prioritize configuration hardening and operational observability first."
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return generate_text(
        prompt=_build_prompt(task, retrieved_context=retrieved_context),
        fallback_text=_build_fallback(task),
    )
