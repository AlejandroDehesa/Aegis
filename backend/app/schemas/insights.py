from pydantic import BaseModel, Field


class InsightsOverviewRead(BaseModel):
    total_tasks: int = 0
    tasks_by_status: dict[str, int] = Field(default_factory=dict)
    tasks_by_task_type: dict[str, int] = Field(default_factory=dict)
    tasks_by_agent_name: dict[str, int] = Field(default_factory=dict)
    feedback_rating_distribution: dict[str, int] = Field(default_factory=dict)
    unrated_tasks: int = 0
    failed_tasks: int = 0
    low_rated_tasks: int = 0
