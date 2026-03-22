from app.services.agent_catalog import get_agent_name_for_task_type


def select_agent(task_type: str) -> str:
    return get_agent_name_for_task_type(task_type)
