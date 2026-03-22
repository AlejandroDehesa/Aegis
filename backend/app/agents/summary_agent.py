from app.models.task import Task


def run_task(task: Task) -> str:
    description = task.description or "No additional context provided."

    return (
        f"Summary for: {task.title}\n\n"
        "Core points:\n"
        f"- Title: {task.title}\n"
        f"- Context: {description}\n"
        "- A concise synthesis has been prepared.\n"
        "- This task fits a summary-oriented workflow."
    )
