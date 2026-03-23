from dataclasses import dataclass
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.task import Task


MEMORY_START_DELIMITER = "=== RECENT TASK MEMORY START ==="
MEMORY_END_DELIMITER = "=== RECENT TASK MEMORY END ==="
MEMORY_SECTION_DELIMITER = "\n\n---\n\n"
MAX_MEMORY_RESULT_CHARS = 320


@dataclass
class MemoryContextResult:
    text: str | None
    task_count: int
    truncated: bool


def _build_result_preview(result_text: str) -> str:
    normalized_text = " ".join(result_text.split())

    if len(normalized_text) <= MAX_MEMORY_RESULT_CHARS:
        return normalized_text

    return f"{normalized_text[:MAX_MEMORY_RESULT_CHARS].rstrip()}..."


def _format_memory_entry(index: int, task: Task) -> str:
    description = task.description or "No description provided."
    result_text = task.result_text or "No result available."

    return (
        f"[Memory {index}]\n"
        f"Title: {task.title}\n"
        f"Description: {description}\n"
        "Result:\n"
        f"{_build_result_preview(result_text)}"
    )


def _build_memory_context(
    tasks: list[Task],
    *,
    max_chars: int,
) -> MemoryContextResult:
    if not tasks:
        return MemoryContextResult(text=None, task_count=0, truncated=False)

    sections: list[str] = []
    task_count = 0
    truncated = False
    current_length = len(MEMORY_START_DELIMITER) + len(MEMORY_END_DELIMITER) + 2

    for index, task in enumerate(tasks, start=1):
        section = _format_memory_entry(index, task)
        separator_length = len(MEMORY_SECTION_DELIMITER) if sections else 0
        projected_length = current_length + separator_length + len(section)

        if projected_length <= max_chars:
            if sections:
                current_length += len(MEMORY_SECTION_DELIMITER)
            sections.append(section)
            current_length += len(section)
            task_count += 1
            continue

        truncated = True
        break

    if not sections:
        return MemoryContextResult(text=None, task_count=0, truncated=truncated)

    context_body = MEMORY_SECTION_DELIMITER.join(sections)
    return MemoryContextResult(
        text=f"{MEMORY_START_DELIMITER}\n{context_body}\n{MEMORY_END_DELIMITER}",
        task_count=task_count,
        truncated=truncated,
    )


def get_recent_task_context_result(
    db: Session,
    user_id: uuid.UUID,
    *,
    current_task_id: uuid.UUID | None = None,
    limit: int | None = None,
) -> MemoryContextResult:
    query = select(Task).where(
        Task.user_id == user_id,
        Task.status == "completed",
        Task.result_text.is_not(None),
    )

    if current_task_id is not None:
        query = query.where(Task.id != current_task_id)

    tasks = db.execute(
        query.order_by(Task.executed_at.desc(), Task.created_at.desc())
        .limit(limit or settings.MEMORY_RECENT_TASK_LIMIT)
    ).scalars().all()

    return _build_memory_context(
        tasks,
        max_chars=settings.MEMORY_MAX_CONTEXT_CHARS,
    )


def get_recent_task_context(
    db: Session,
    user_id: uuid.UUID,
    *,
    current_task_id: uuid.UUID | None = None,
    limit: int | None = None,
) -> str | None:
    return get_recent_task_context_result(
        db,
        user_id,
        current_task_id=current_task_id,
        limit=limit,
    ).text
