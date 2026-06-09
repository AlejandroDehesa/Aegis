from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import BackgroundTasks
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.tasks import (
    create_task,
    execute_user_task,
    list_tasks,
    submit_task_feedback,
)
from app.schemas.task import TaskCreate, TaskFeedbackUpdate
from app.services.task_executor import (
    TaskExecutionResult,
    TaskExecutionStateError,
)

from .helpers import FakeExecuteResult, build_task, build_user


class TasksTests(unittest.TestCase):
    def test_create_task_assigns_classification_and_agent(self) -> None:
        db = MagicMock()
        user = build_user()

        with (
            patch("app.api.v1.tasks.classify_task", return_value="comparison"),
            patch("app.api.v1.tasks.select_agent", return_value="ComparisonAgent"),
        ):
            task = create_task(
                TaskCreate(title="Compare A and B", description="Need tradeoffs"),
                current_user=user,
                db=db,
            )

        self.assertEqual(task.task_type, "comparison")
        self.assertEqual(task.agent_name, "ComparisonAgent")
        db.add.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once()

    def test_list_tasks_supports_filters(self) -> None:
        db = MagicMock()
        user = build_user()
        db.execute.return_value = FakeExecuteResult(
            scalar_values=[build_task(user_id=user.id, status="failed", feedback_rating=2)],
        )

        tasks = list_tasks(
            task_status="failed",
            task_type="comparison",
            agent_name="ComparisonAgent",
            feedback_rating=2,
            current_user=user,
            db=db,
        )

        query = db.execute.call_args[0][0]
        query_text = str(query)
        self.assertIn("tasks.status", query_text)
        self.assertIn("tasks.task_type", query_text)
        self.assertIn("tasks.agent_name", query_text)
        self.assertIn("tasks.feedback_rating", query_text)
        self.assertEqual(len(tasks), 1)

    def test_list_tasks_applies_pagination_and_stable_order(self) -> None:
        db = MagicMock()
        user = build_user()
        db.execute.return_value = FakeExecuteResult(
            scalar_values=[build_task(user_id=user.id)],
        )

        list_tasks(
            current_user=user,
            db=db,
            limit=20,
            offset=40,
        )

        query_text = str(db.execute.call_args[0][0])
        self.assertIn("ORDER BY tasks.created_at DESC, tasks.id DESC", query_text)
        self.assertIn("LIMIT", query_text)
        self.assertIn("OFFSET", query_text)

    def test_execute_user_task_maps_state_error_to_http_409(self) -> None:
        db = MagicMock()
        user = build_user()
        task = build_task(user_id=user.id, status="processing")

        with (
            patch("app.api.v1.tasks._get_user_task", return_value=task),
            patch(
                "app.api.v1.tasks.execute_task",
                side_effect=TaskExecutionStateError("cannot execute"),
            ),
        ):
            with self.assertRaises(HTTPException) as context:
                execute_user_task(
                    task.id,
                    current_user=user,
                    db=db,
                    background_tasks=BackgroundTasks(),
                )

        self.assertEqual(context.exception.status_code, 409)

    def test_execute_user_task_success_returns_task_read(self) -> None:
        db = MagicMock()
        user = build_user()
        task = build_task(user_id=user.id, status="completed")
        execution_result = TaskExecutionResult(task=task, rag_debug=None)

        with (
            patch("app.api.v1.tasks._get_user_task", return_value=task),
            patch("app.api.v1.tasks.execute_task", return_value=execution_result),
        ):
            response = execute_user_task(
                task.id,
                current_user=user,
                db=db,
                background_tasks=BackgroundTasks(),
            )

        self.assertEqual(response.id, task.id)

    def test_submit_feedback_requires_finished_task(self) -> None:
        db = MagicMock()
        user = build_user()
        task = build_task(user_id=user.id, status="processing")

        with patch("app.api.v1.tasks._get_user_task", return_value=task):
            with self.assertRaises(HTTPException) as context:
                submit_task_feedback(
                    task.id,
                    TaskFeedbackUpdate(feedback_rating=4, feedback_comment="good"),
                    current_user=user,
                    db=db,
                )

        self.assertEqual(context.exception.status_code, 409)

    def test_submit_feedback_persists_rating_and_comment(self) -> None:
        db = MagicMock()
        user = build_user()
        task = build_task(user_id=user.id, status="completed")

        with patch("app.api.v1.tasks._get_user_task", return_value=task):
            updated = submit_task_feedback(
                task.id,
                TaskFeedbackUpdate(feedback_rating=5, feedback_comment="Very useful result"),
                current_user=user,
                db=db,
            )

        self.assertEqual(updated.feedback_rating, 5)
        self.assertEqual(updated.feedback_comment, "Very useful result")
        self.assertIsNotNone(updated.feedback_submitted_at)
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(task)

    def test_task_create_rejects_blank_title(self) -> None:
        with self.assertRaises(ValidationError):
            TaskCreate(title="   ", description="Anything")

    def test_task_create_limits_description_length(self) -> None:
        with self.assertRaises(ValidationError):
            TaskCreate(title="Valid title", description="x" * 5001)

    def test_task_create_normalizes_blank_description_to_none(self) -> None:
        task = TaskCreate(title="Valid title", description="   ")
        self.assertIsNone(task.description)

    def test_feedback_comment_blank_is_normalized_to_none(self) -> None:
        feedback = TaskFeedbackUpdate(feedback_rating=4, feedback_comment="   ")
        self.assertIsNone(feedback.feedback_comment)


if __name__ == "__main__":
    unittest.main()
