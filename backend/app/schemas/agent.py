from pydantic import BaseModel


class AgentRead(BaseModel):
    name: str
    description: str
    supported_task_types: list[str]
