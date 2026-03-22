from app.services.task_classifier import (
    TASK_TYPE_COMPARISON,
    TASK_TYPE_GENERAL,
    TASK_TYPE_RESEARCH,
    TASK_TYPE_SUMMARY,
)


TASK_TYPE_TO_AGENT = {
    TASK_TYPE_RESEARCH: "ResearchAgent",
    TASK_TYPE_SUMMARY: "SummaryAgent",
    TASK_TYPE_COMPARISON: "ComparisonAgent",
    TASK_TYPE_GENERAL: "GeneralAssistantAgent",
}


def select_agent(task_type: str) -> str:
    return TASK_TYPE_TO_AGENT.get(task_type, "GeneralAssistantAgent")
