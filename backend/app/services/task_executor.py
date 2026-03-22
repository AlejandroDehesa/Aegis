from sqlalchemy.orm import Session

from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.general_assistant_agent import run_task as run_general_task
from app.agents.research_agent import run_task as run_research_task
from app.agents.summary_agent import run_task as run_summary_task
from app.models.task import Task


TASK_STATUS_PENDING = "pending"
TASK_STATUS_PROCESSING = "processing"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"


AGENT_RUNNERS = {
    "ResearchAgent": run_research_task,
    "SummaryAgent": run_summary_task,
    "ComparisonAgent": run_comparison_task,
    "GeneralAssistantAgent": run_general_task,
}


class TaskExecutionError(Exception):
    pass


def execute_task(task: Task, db: Session) -> Task:
    runner = AGENT_RUNNERS.get(task.agent_name)

    if runner is None:
        task.status = TASK_STATUS_FAILED
        task.result_text = "Task execution failed."
        db.add(task)
        db.commit()
        db.refresh(task)
        raise TaskExecutionError("No execution strategy found for the selected agent.")

    task.status = TASK_STATUS_PROCESSING
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        result_text = runner(task)
        task.result_text = result_text
        task.status = TASK_STATUS_COMPLETED
    except Exception as error:
        task.result_text = "Task execution failed."
        task.status = TASK_STATUS_FAILED
        db.add(task)
        db.commit()
        db.refresh(task)
        raise TaskExecutionError("Task execution failed.") from error

    db.add(task)
    db.commit()
    db.refresh(task)

    return task
