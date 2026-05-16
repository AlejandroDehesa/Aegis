from app.services.task_classifier import (
    TASK_TYPE_ANALYSIS,
    TASK_TYPE_COMPARISON,
    TASK_TYPE_GENERAL,
    TASK_TYPE_PLANNING,
    TASK_TYPE_RESEARCH,
    TASK_TYPE_SUMMARY,
)


AGENT_CATALOG = [
    {
        "name": "ResearchAgent",
        "description": "Handles research-oriented tasks and exploratory analysis.",
        "supported_task_types": [TASK_TYPE_RESEARCH],
    },
    {
        "name": "SummaryAgent",
        "description": "Generates concise summaries from the task input.",
        "supported_task_types": [TASK_TYPE_SUMMARY],
    },
    {
        "name": "ComparisonAgent",
        "description": "Produces structured comparisons between options or approaches.",
        "supported_task_types": [TASK_TYPE_COMPARISON],
    },
    {
        "name": "AnalysisAgent",
        "description": "Assesses risks, impact, and mitigations for analytical tasks.",
        "supported_task_types": [TASK_TYPE_ANALYSIS],
    },
    {
        "name": "PlanningAgent",
        "description": "Creates practical step-by-step execution plans.",
        "supported_task_types": [TASK_TYPE_PLANNING],
    },
    {
        "name": "GeneralAssistantAgent",
        "description": "Handles general-purpose tasks that do not fit a specialized category.",
        "supported_task_types": [TASK_TYPE_GENERAL],
    },
]


DEFAULT_AGENT_NAME = "GeneralAssistantAgent"


def list_agents() -> list[dict]:
    return AGENT_CATALOG


def get_agent_name_for_task_type(task_type: str) -> str:
    for agent in AGENT_CATALOG:
        if task_type in agent["supported_task_types"]:
            return agent["name"]

    return DEFAULT_AGENT_NAME
