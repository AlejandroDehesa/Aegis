from app.models.task import Task


def run_task(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        f"General assistance output for: {task.title}\n\n"
        f"Request:\n- {task.title}\n"
        f"Context:\n- {description}\n\n"
        "Suggested next step:\n"
        "- The task has been processed with the general assistant workflow.\n"
        "- It is ready for future expansion with richer agent capabilities."
    )
