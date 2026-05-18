from app.agents.execution_result import AgentExecutionResult
from app.agents.prompt_utils import build_retrieved_context_block
from app.models.task import Task
from app.services.llm.schemas import LLMRequest
from app.services.llm_service import generate


def _build_prompt(task: Task, retrieved_context: str | None = None) -> str:
    description = task.description or "No additional analysis context provided."
    context_block = build_retrieved_context_block(retrieved_context)

    return (
        "You are AnalysisAgent inside Aegis.\n"
        "Deliver a practical and decision-oriented risk analysis.\n"
        "Avoid placeholders and ensure the output references the task specifics.\n\n"
        f"Task title: {task.title}\n"
        f"Task description: {description}\n\n"
        f"{context_block}"
        "Output format (use these exact section headings):\n"
        "1. Executive summary\n"
        "2. Key risks\n"
        "3. Impact\n"
        "4. Probability / severity\n"
        "5. Mitigation\n"
        "6. Priority\n"
        "7. Final recommendation"
    )


def _build_fallback(task: Task) -> str:
    description = task.description or "No additional analysis context provided."

    return (
        "Executive summary:\n"
        f"- Risk analysis prepared for: {task.title}\n\n"
        "Key risks:\n"
        "- Risk 1: Deployment instability due to environment misconfiguration.\n"
        "- Risk 2: Service interruption under load spikes.\n\n"
        "Impact:\n"
        "- Delays in delivery and degraded user experience.\n\n"
        "Probability / severity:\n"
        "- Risk 1: medium probability, high severity.\n"
        "- Risk 2: medium probability, medium-high severity.\n\n"
        "Mitigation:\n"
        "- Use staged rollout, health checks, and rollback plan.\n"
        "- Add monitoring and capacity alerts before release.\n\n"
        "Priority:\n"
        "- Priority 1: configuration hardening and release safeguards.\n"
        "- Priority 2: observability and capacity management.\n\n"
        f"Context considered: {description}\n\n"
        "Final recommendation:\n"
        "- Prioritize configuration hardening and operational observability first."
    )


def run_task(task: Task, retrieved_context: str | None = None) -> str:
    return run_task_with_metadata(task, retrieved_context=retrieved_context).text


def run_task_with_metadata(task: Task, retrieved_context: str | None = None) -> AgentExecutionResult:
    response = generate(
        request=LLMRequest(prompt=_build_prompt(task, retrieved_context=retrieved_context)),
        fallback_text=_build_fallback(task),
    )
    return AgentExecutionResult.from_llm_response(response)
