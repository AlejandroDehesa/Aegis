from fastapi import APIRouter

from app.schemas.agent import AgentRead
from app.services.agent_catalog import list_agents


router = APIRouter()


@router.get("/agents", response_model=list[AgentRead])
def get_agents() -> list[dict]:
    return list_agents()
