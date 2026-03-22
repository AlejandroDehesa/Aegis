from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead


router = APIRouter()


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = Task(
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("/tasks", response_model=list[TaskRead])
def list_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Task]:
    tasks = db.execute(
        select(Task)
        .where(Task.user_id == current_user.id)
        .order_by(Task.created_at.desc())
    ).scalars().all()

    return tasks
