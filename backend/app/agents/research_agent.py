from app.models.task import Task


def run_task(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        f"Research overview for: {task.title}\n\n"
        f"Objective:\n- {task.title}\n\n"
        f"Context:\n- {description}\n\n"
        "Initial findings:\n"
        "- Key topics have been identified for further investigation.\n"
        "- A deeper source-by-source analysis can be executed in a future phase.\n"
        "- This task is suitable for a research-oriented workflow."
    )
