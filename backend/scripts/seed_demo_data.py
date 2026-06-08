from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.task import Task
from app.models.user import User


DEMO_EMAIL = "demo@aegis.local"
DEMO_PASSWORD = "Demo12345!"


def _build_trace(
    *,
    task_type: str,
    agent_name: str,
    started_at: datetime,
    finished_at: datetime,
    status: str = "completed",
) -> list[dict[str, object]]:
    duration_ms = max(int((finished_at - started_at).total_seconds() * 1000), 0)
    classification_finished = started_at + timedelta(milliseconds=200)
    selection_finished = classification_finished + timedelta(milliseconds=200)

    return [
        {
            "step_index": 1,
            "step_number": 1,
            "step_name": "classification",
            "agent_name": "TaskClassifier",
            "status": "completed",
            "short_summary": f"Task classified as '{task_type}'.",
            "started_at": started_at.isoformat(),
            "finished_at": classification_finished.isoformat(),
            "duration_ms": 200,
        },
        {
            "step_index": 2,
            "step_number": 2,
            "step_name": "agent_selection",
            "agent_name": agent_name,
            "status": "completed",
            "short_summary": f"Selected execution pipeline agents: {agent_name}.",
            "started_at": classification_finished.isoformat(),
            "finished_at": selection_finished.isoformat(),
            "duration_ms": 200,
        },
        {
            "step_index": 3,
            "step_number": 3,
            "step_name": "execution",
            "agent_name": agent_name,
            "status": status,
            "short_summary": "Execution completed with a user-ready response."
            if status == "completed"
            else "Execution failed and was recorded for review.",
            "started_at": selection_finished.isoformat(),
            "finished_at": finished_at.isoformat(),
            "duration_ms": max(duration_ms - 400, 0),
        },
    ]


def build_demo_task_templates(now: datetime) -> list[dict[str, object]]:
    comparison_started = now - timedelta(minutes=18)
    comparison_finished = now - timedelta(minutes=17, seconds=35)

    analysis_started = now - timedelta(minutes=16)
    analysis_finished = now - timedelta(minutes=15, seconds=42)

    planning_started = now - timedelta(minutes=13)
    planning_finished = now - timedelta(minutes=12, seconds=31)

    summary_started = now - timedelta(minutes=10)
    summary_finished = now - timedelta(minutes=9, seconds=40)

    research_started = now - timedelta(minutes=7)
    research_finished = now - timedelta(minutes=6, seconds=29)

    return [
        {
            "title": "Compare FastAPI and Django for an AI orchestration backend",
            "description": (
                "Compare FastAPI and Django for a modern backend API. Include advantages, "
                "disadvantages, ideal use cases, and a final recommendation."
            ),
            "task_type": "comparison",
            "agent_name": "ComparisonAgent",
            "status": "completed",
            "result_text": (
                "FastAPI provides faster iteration for API-first services and strong async support, "
                "which helps when orchestrating agent workflows. Django offers a mature ecosystem, "
                "integrated admin, and robust conventions for larger monolithic products.\n\n"
                "Advantages / Pros:\n"
                "- FastAPI: high development speed for typed APIs and asynchronous I/O.\n"
                "- Django: built-in admin and broader batteries-included components.\n\n"
                "Disadvantages / Cons:\n"
                "- FastAPI: fewer built-in enterprise modules out of the box.\n"
                "- Django: heavier framework overhead for lightweight API-only services.\n\n"
                "Recommendation:\n"
                "- Choose FastAPI for API-first orchestration platforms like Aegis.\n"
                "- Choose Django when integrated admin and full-stack conventions are the priority."
            ),
            "started_at": comparison_started,
            "finished_at": comparison_finished,
            "duration_ms": max(int((comparison_finished - comparison_started).total_seconds() * 1000), 0),
            "executed_at": comparison_finished,
            "feedback_rating": 5,
            "feedback_comment": "Useful comparison with clear recommendation for demo decisions.",
            "feedback_submitted_at": now - timedelta(minutes=16, seconds=55),
            "execution_trace": _build_trace(
                task_type="comparison",
                agent_name="ComparisonAgent",
                started_at=comparison_started,
                finished_at=comparison_finished,
            ),
        },
        {
            "title": "Analyze deployment risks for Docker + PostgreSQL on Railway",
            "description": (
                "Analyze the risks of deploying an API backend with Docker and PostgreSQL on Railway. "
                "Include risk, impact, mitigation, and recommendation."
            ),
            "task_type": "analysis",
            "agent_name": "AnalysisAgent",
            "status": "completed",
            "result_text": (
                "Risk analysis:\n"
                "- Risk: container misconfiguration can break startup ordering.\n"
                "- Risk: constrained memory can impact PostgreSQL performance.\n\n"
                "Impact:\n"
                "- Startup failures and unstable response times during peak usage.\n\n"
                "Mitigation:\n"
                "- Add explicit health checks, startup dependencies, and resource limits.\n"
                "- Configure connection pooling and monitor saturation alerts.\n\n"
                "Recommendation:\n"
                "- Validate runtime configuration in staging and gate release on health metrics."
            ),
            "started_at": analysis_started,
            "finished_at": analysis_finished,
            "duration_ms": max(int((analysis_finished - analysis_started).total_seconds() * 1000), 0),
            "executed_at": analysis_finished,
            "feedback_rating": 4,
            "feedback_comment": "Good risk framing and practical mitigations.",
            "feedback_submitted_at": now - timedelta(minutes=14, seconds=59),
            "execution_trace": _build_trace(
                task_type="analysis",
                agent_name="AnalysisAgent",
                started_at=analysis_started,
                finished_at=analysis_finished,
            ),
        },
        {
            "title": "Plan a phased rollout for Aegis task orchestration",
            "description": (
                "Create a step-by-step plan for classification, agent selection, execution trace, "
                "feedback loop, and insights."
            ),
            "task_type": "planning",
            "agent_name": "PlanningAgent",
            "status": "completed",
            "result_text": (
                "1. Define acceptance criteria for each core flow (create, execute, trace, feedback).\n"
                "2. Stabilize backend contracts and task lifecycle assertions.\n"
                "3. Harden frontend integration with smoke checks for detail and insights views.\n"
                "4. Validate documents upload and retrieval fallback behavior.\n"
                "5. Rehearse demo script with seeded data and capture expected outputs.\n\n"
                "Next action:\n"
                "- Execute regression suite for comparison, analysis, and planning flows."
            ),
            "started_at": planning_started,
            "finished_at": planning_finished,
            "duration_ms": max(int((planning_finished - planning_started).total_seconds() * 1000), 0),
            "executed_at": planning_finished,
            "feedback_rating": 5,
            "feedback_comment": "Plan is clear, ordered, and demo-ready.",
            "feedback_submitted_at": now - timedelta(minutes=11, seconds=48),
            "execution_trace": _build_trace(
                task_type="planning",
                agent_name="PlanningAgent",
                started_at=planning_started,
                finished_at=planning_finished,
            ),
        },
        {
            "title": "Summarize backend reliability improvements for sprint review",
            "description": (
                "Summarize the key backend reliability changes made this sprint for non-technical stakeholders."
            ),
            "task_type": "summary",
            "agent_name": "SummaryAgent",
            "status": "completed",
            "result_text": (
                "Summary:\n"
                "- We improved task classification coverage in Spanish and English.\n"
                "- We enforced minimum output quality checks to avoid weak responses.\n"
                "- We standardized execution trace steps for reliable task detail views.\n"
                "- We aligned seed data with the current schema for consistent demos.\n"
                "- We added regression tests to keep critical flows stable."
            ),
            "started_at": summary_started,
            "finished_at": summary_finished,
            "duration_ms": max(int((summary_finished - summary_started).total_seconds() * 1000), 0),
            "executed_at": summary_finished,
            "execution_trace": _build_trace(
                task_type="summary",
                agent_name="SummaryAgent",
                started_at=summary_started,
                finished_at=summary_finished,
            ),
        },
        {
            "title": "Research backend observability options for Aegis",
            "description": (
                "Research practical observability options to monitor API health, task execution outcomes, "
                "and quality feedback trends."
            ),
            "task_type": "research",
            "agent_name": "ResearchAgent",
            "status": "completed",
            "result_text": (
                "Research findings:\n"
                "- Structured logging plus request IDs improves traceability quickly.\n"
                "- Metrics for task statuses and execution durations provide fast operational visibility.\n"
                "- Error-rate alerts tied to failed tasks help catch regressions early.\n\n"
                "Recommendation:\n"
                "- Start with logs + status metrics + simple alerting before adding complex tooling."
            ),
            "started_at": research_started,
            "finished_at": research_finished,
            "duration_ms": max(int((research_finished - research_started).total_seconds() * 1000), 0),
            "executed_at": research_finished,
            "execution_trace": _build_trace(
                task_type="research",
                agent_name="ResearchAgent",
                started_at=research_started,
                finished_at=research_finished,
            ),
        },
    ]


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

        task_templates = build_demo_task_templates(now)

        created = 0
        updated = 0

        for template in task_templates:
            existing_task = existing_tasks.get(template["title"])

            if existing_task is not None:
                has_trace = bool(existing_task.execution_trace)
                needs_feedback_update = (
                    template.get("feedback_rating") is not None and existing_task.feedback_rating is None
                )
                needs_trace_update = not has_trace and bool(template.get("execution_trace"))

                if needs_feedback_update or needs_trace_update:
                    if needs_feedback_update:
                        existing_task.feedback_rating = template.get("feedback_rating")
                        existing_task.feedback_comment = template.get("feedback_comment")
                        existing_task.feedback_submitted_at = template.get("feedback_submitted_at")
                    if needs_trace_update:
                        existing_task.execution_trace = template.get("execution_trace") or []
                    db.add(existing_task)
                    updated += 1
                continue

            task = Task(user_id=user.id, **template)
            db.add(task)
            created += 1

        if created or updated:
            db.commit()

        print(f"Seed complete. Created {created} demo task(s), updated {updated}.")


def ensure_schema_ready() -> None:
    try:
        with SessionLocal() as db:
            db.execute(select(User.id).limit(1))
    except Exception as error:
        raise RuntimeError(
            "Database schema is not ready. Run `alembic upgrade head` before seeding demo data."
        ) from error


def main() -> None:
    ensure_schema_ready()
    user = get_or_create_demo_user()
    seed_demo_tasks(user)
    print("Demo credentials:")
    print(f"  email: {DEMO_EMAIL}")
    print(f"  password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
