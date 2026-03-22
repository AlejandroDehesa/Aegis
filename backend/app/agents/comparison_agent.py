from app.models.task import Task


def run_task(task: Task) -> str:
    description = task.description or "No additional comparison context provided."

    return (
        f"Comparison analysis for: {task.title}\n\n"
        "Comparison frame:\n"
        f"- Subject: {task.title}\n"
        f"- Notes: {description}\n\n"
        "Structured output:\n"
        "- Item A: requires evaluation.\n"
        "- Item B: requires evaluation.\n"
        "- Final recommendation can be expanded in future execution phases."
    )
