import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.auth import get_current_user
from app.core.database import get_db
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead
from app.services.agent_selector import select_agent
from app.services.task_classifier import classify_task


router = APIRouter()


@router.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task_type = classify_task(
        title=task_in.title,
        description=task_in.description,
    )
    agent_name = select_agent(task_type)

    task = Task(
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        task_type=task_type,
        agent_name=agent_name,
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


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    return task
