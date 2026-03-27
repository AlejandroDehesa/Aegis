from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.insights import InsightsOverviewRead


router = APIRouter()


def _to_distribution(rows: list[tuple[object, int]], *, key_fallback: str) -> dict[str, int]:
    distribution: dict[str, int] = {}

    for raw_key, count in rows:
        key = str(raw_key) if raw_key is not None else key_fallback
        distribution[key] = int(count)

    return distribution


@router.get("/insights/overview", response_model=InsightsOverviewRead)
def read_insights_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InsightsOverviewRead:
    user_filter = Task.user_id == current_user.id

    total_tasks = db.scalar(
        select(func.count(Task.id)).where(user_filter)
    ) or 0

    status_rows = db.execute(
        select(Task.status, func.count(Task.id))
        .where(user_filter)
        .group_by(Task.status)
    ).all()

    task_type_rows = db.execute(
        select(Task.task_type, func.count(Task.id))
        .where(user_filter)
        .group_by(Task.task_type)
    ).all()

    agent_rows = db.execute(
        select(Task.agent_name, func.count(Task.id))
        .where(user_filter)
        .group_by(Task.agent_name)
    ).all()

    feedback_rows = db.execute(
        select(Task.feedback_rating, func.count(Task.id))
        .where(user_filter, Task.feedback_rating.is_not(None))
        .group_by(Task.feedback_rating)
    ).all()

    unrated_tasks = db.scalar(
        select(func.count(Task.id))
        .where(user_filter, Task.feedback_rating.is_(None))
    ) or 0

    failed_tasks = db.scalar(
        select(func.count(Task.id))
        .where(user_filter, Task.status == "failed")
    ) or 0

    low_rated_tasks = db.scalar(
        select(func.count(Task.id))
        .where(user_filter, Task.feedback_rating.is_not(None), Task.feedback_rating <= 2)
    ) or 0

    return InsightsOverviewRead(
        total_tasks=int(total_tasks),
        tasks_by_status=_to_distribution(status_rows, key_fallback="unknown"),
        tasks_by_task_type=_to_distribution(task_type_rows, key_fallback="unknown"),
        tasks_by_agent_name=_to_distribution(agent_rows, key_fallback="unknown"),
        feedback_rating_distribution=_to_distribution(feedback_rows, key_fallback="unrated"),
        unrated_tasks=int(unrated_tasks),
        failed_tasks=int(failed_tasks),
        low_rated_tasks=int(low_rated_tasks),
    )
