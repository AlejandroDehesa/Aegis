from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import BackgroundTasks

from app.api.v1.insights import read_insights_overview
from app.api.v1.tasks import create_task, execute_user_task, get_task_trace, submit_task_feedback
from app.schemas.task import TaskCreate, TaskFeedbackUpdate
from app.services.task_executor import TaskExecutionResult

from .helpers import FakeExecuteResult, build_task, build_user


class CriticalFlowTests(unittest.TestCase):
    def test_critical_flow_create_execute_trace_feedback_insights(self) -> None:
        db = MagicMock()
        user = build_user()

        with (
            patch("app.api.v1.tasks.classify_task", return_value="research"),
            patch("app.api.v1.tasks.select_agent", return_value="ResearchAgent"),
        ):
            created_task = create_task(
                TaskCreate(
                    title="Investigate orchestration quality trends",
                    description="Need practical findings",
                ),
                current_user=user,
                db=db,
            )

        executed_task = build_task(
            id=created_task.id,
            user_id=user.id,
            title=created_task.title,
            description=created_task.description,
            status="completed",
            task_type="research",
            agent_name="ResearchAgent",
            result_text="Operational summary generated successfully.",
            execution_trace=[
                {
                    "step_name": "execution",
                    "agent_name": "ResearchAgent",
                    "status": "completed",
                }
            ],
        )

        with (
            patch("app.api.v1.tasks._get_user_task", return_value=executed_task),
            patch(
                "app.api.v1.tasks.execute_task",
                return_value=TaskExecutionResult(task=executed_task, rag_debug=None),
            ),
        ):
            execute_user_task(
                executed_task.id,
                current_user=user,
                db=db,
                background_tasks=BackgroundTasks(),
            )

        with patch("app.api.v1.tasks._get_user_task", return_value=executed_task):
            trace = get_task_trace(executed_task.id, current_user=user, db=db)
            self.assertEqual(trace.status, "completed")
            self.assertEqual(len(trace.execution_trace), 1)

            submit_task_feedback(
                executed_task.id,
                TaskFeedbackUpdate(feedback_rating=4, feedback_comment="Solid quality"),
                current_user=user,
                db=db,
            )
            self.assertEqual(executed_task.feedback_rating, 4)

        db.scalar.side_effect = [1, 0, 0, 0]
        db.execute.side_effect = [
            FakeExecuteResult(rows=[("completed", 1)]),
            FakeExecuteResult(rows=[("research", 1)]),
            FakeExecuteResult(rows=[("ResearchAgent", 1)]),
            FakeExecuteResult(rows=[(4, 1)]),
        ]
        overview = read_insights_overview(current_user=user, db=db)
        self.assertEqual(overview.total_tasks, 1)
        self.assertEqual(overview.feedback_rating_distribution["4"], 1)


if __name__ == "__main__":
    unittest.main()
