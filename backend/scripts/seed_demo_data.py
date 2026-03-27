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
        existing_titles = set(
            db.execute(
                select(Task.title).where(Task.user_id == user.id)
            ).scalars().all()
        )

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
                "execution_trace": [
                    {
                        "step": "classification",
                        "status": "completed",
                        "summary": "Task classified as comparison.",
                    },
                    {
                        "step": "agent_selection",
                        "status": "completed",
                        "summary": "ComparisonAgent selected.",
                    },
                    {
                        "step": "execution",
                        "status": "completed",
                        "summary": "Comparison response generated successfully.",
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

        for template in task_templates:
            if template["title"] in existing_titles:
                continue

            task = Task(user_id=user.id, **template)
            db.add(task)
            created += 1

        if created:
            db.commit()

        print(f"Seed complete. Created {created} demo task(s).")


def main() -> None:
    create_tables()
    user = get_or_create_demo_user()
    seed_demo_tasks(user)
    print("Demo credentials:")
    print(f"  email: {DEMO_EMAIL}")
    print(f"  password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
