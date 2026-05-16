from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal, create_tables
from app.core.security import hash_password
from app.models.task import Task
from app.models.user import User


DEMO_EMAIL = "demo@aegis.local"
DEMO_PASSWORD = "Demo12345!"


def get_or_create_demo_user() -> User:
    with SessionLocal() as db:
        user = db.execute(
            select(User).where(User.email == DEMO_EMAIL)
        ).scalar_one_or_none()

        if user is not None:
            return user

        user = User(
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def seed_demo_tasks(user: User) -> None:
    with SessionLocal() as db:
        existing_tasks = {
            task.title: task
            for task in db.execute(
                select(Task).where(Task.user_id == user.id)
            ).scalars().all()
        }

        now = datetime.now(UTC)

        task_templates = [
            {
                "title": "Compare FastAPI and Django for internal AI orchestration",
                "description": "Generate a practical backend-focused comparison for Aegis.",
                "task_type": "comparison",
                "agent_name": "ComparisonAgent",
                "status": "completed",
                "result_text": (
                    "FastAPI offers faster API iteration and clearer async support for "
                    "Aegis orchestration endpoints. Django remains strong for broader "
                    "admin-heavy products."
                ),
                "started_at": now - timedelta(minutes=7),
                "finished_at": now - timedelta(minutes=6, seconds=35),
                "duration_ms": 25000,
                "executed_at": now - timedelta(minutes=6, seconds=35),
                "feedback_rating": 5,
                "feedback_comment": "Clear output and useful tradeoffs for a backend-first decision.",
                "feedback_submitted_at": now - timedelta(minutes=5, seconds=50),
                "execution_trace": [
                    {
                        "step_index": 1,
                        "step_name": "classification",
                        "agent_name": "TaskClassifier",
                        "status": "completed",
                        "short_summary": "Task classified as comparison.",
                    },
                    {
                        "step_index": 2,
                        "step_name": "agent_selection",
                        "agent_name": "ComparisonAgent",
                        "status": "completed",
                        "short_summary": "ComparisonAgent selected.",
                    },
                    {
                        "step_index": 3,
                        "step_name": "execution",
                        "agent_name": "ComparisonAgent",
                        "status": "completed",
                        "short_summary": "Comparison response generated successfully.",
                    },
                ],
            },
            {
                "title": "Summarize latest architecture notes for demo",
                "description": "Produce a concise summary for the product walkthrough.",
                "task_type": "summary",
                "agent_name": "SummaryAgent",
                "status": "pending",
                "execution_trace": [],
            },
        ]

        created = 0
        updated = 0

        for template in task_templates:
            existing_task = existing_tasks.get(template["title"])

            if existing_task is not None:
                if template.get("feedback_rating") and existing_task.feedback_rating is None:
                    existing_task.feedback_rating = template["feedback_rating"]
                    existing_task.feedback_comment = template.get("feedback_comment")
                    existing_task.feedback_submitted_at = template.get("feedback_submitted_at")
                    db.add(existing_task)
                    updated += 1
                continue

            task = Task(user_id=user.id, **template)
            db.add(task)
            created += 1

        if created or updated:
            db.commit()

        print(f"Seed complete. Created {created} demo task(s), updated {updated}.")


def main() -> None:
    create_tables()
    user = get_or_create_demo_user()
    seed_demo_tasks(user)
    print("Demo credentials:")
    print(f"  email: {DEMO_EMAIL}")
    print(f"  password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
