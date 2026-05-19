from __future__ import annotations

import unittest
from datetime import UTC, datetime
import uuid
from unittest.mock import MagicMock, patch

from fastapi import BackgroundTasks, HTTPException

from app.api.v1.tasks import _serialize_task, execute_user_task, get_task, get_task_trace, list_tasks
from app.services.task_executor import (
    TASK_STATUS_QUEUED,
    TASK_STATUS_FAILED,
    TaskExecutionResult,
    TaskExecutionStateError,
    execute_task,
    get_task_execution_mode,
    queue_task_for_background,
    run_task_execution_background,
)
from tests.helpers import FakeExecuteResult, build_task, build_user


class TaskBackgroundExecutionTests(unittest.TestCase):
    def test_execute_task_in_sync_mode_completes_immediately(self) -> None:
        db = MagicMock()
        user = build_user()
        task = build_task(user_id=user.id, status="pending")
        completed = build_task(id=task.id, user_id=user.id, status="completed")

        with (
            patch("app.api.v1.tasks._get_user_task", return_value=task),
            patch("app.api.v1.tasks.get_task_execution_mode", return_value="sync"),
            patch(
                "app.api.v1.tasks.execute_task",
                return_value=TaskExecutionResult(task=completed, rag_debug=None),
            ) as execute_mock,
        ):
            response = execute_user_task(
                task.id,
                current_user=user,
                db=db,
                background_tasks=BackgroundTasks(),
            )

        self.assertEqual(response.status, "completed")
        execute_mock.assert_called_once()

    def test_execute_task_in_background_mode_returns_queued(self) -> None:
        db = MagicMock()
        user = build_user()
        task = build_task(user_id=user.id, status="pending")
        queued = build_task(
            id=task.id,
            user_id=user.id,
            status=TASK_STATUS_QUEUED,
            execution_trace=[{"step_name": "queued", "agent_name": "TaskExecutor", "status": "completed"}],
        )
        background_tasks = BackgroundTasks()

        with (
            patch("app.api.v1.tasks._get_user_task", return_value=task),
            patch("app.api.v1.tasks.get_task_execution_mode", return_value="background"),
            patch("app.api.v1.tasks.queue_task_for_background", return_value=queued),
            patch("app.api.v1.tasks.execute_task") as execute_mock,
        ):
            response = execute_user_task(
                task.id,
                current_user=user,
                db=db,
                background_tasks=background_tasks,
            )

        self.assertEqual(response.status, "queued")
        self.assertEqual(len(background_tasks.tasks), 1)
        execute_mock.assert_not_called()

    def test_execute_task_does_not_start_duplicate_when_processing(self) -> None:
        db = MagicMock()
        user = build_user()
        task = build_task(user_id=user.id, status="processing")
        background_tasks = BackgroundTasks()

        with (
            patch("app.api.v1.tasks._get_user_task", return_value=task),
            patch("app.api.v1.tasks.get_task_execution_mode", return_value="background"),
            patch(
                "app.api.v1.tasks.queue_task_for_background",
                side_effect=TaskExecutionStateError("Task cannot be executed from status 'processing'."),
            ),
        ):
            with self.assertRaises(HTTPException) as context:
                execute_user_task(
                    task.id,
                    current_user=user,
                    db=db,
                    background_tasks=background_tasks,
                )

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(len(background_tasks.tasks), 0)

    def test_execute_task_not_found(self) -> None:
        db = MagicMock()
        user = build_user()
        task_id = uuid.uuid4()

        with patch(
            "app.api.v1.tasks._get_user_task",
            side_effect=HTTPException(status_code=404, detail="Task not found"),
        ):
            with self.assertRaises(HTTPException) as context:
                execute_user_task(
                    task_id,
                    current_user=user,
                    db=db,
                    background_tasks=BackgroundTasks(),
                )

        self.assertEqual(context.exception.status_code, 404)

    def test_execute_task_forbidden_for_other_user(self) -> None:
        db = MagicMock()
        user = build_user()
        other_user_task = build_task(user_id=uuid.uuid4(), status="pending")

        with patch(
            "app.api.v1.tasks._get_user_task",
            side_effect=HTTPException(status_code=404, detail="Task not found"),
        ):
            with self.assertRaises(HTTPException) as context:
                execute_user_task(
                    other_user_task.id,
                    current_user=user,
                    db=db,
                    background_tasks=BackgroundTasks(),
                )

        # Intentional 404 to avoid leaking ownership.
        self.assertEqual(context.exception.status_code, 404)

    def test_execute_completed_task_behavior_is_stable(self) -> None:
        db = MagicMock()
        user = build_user()
        completed_task = build_task(user_id=user.id, status="completed")
        background_tasks = BackgroundTasks()

        with (
            patch("app.api.v1.tasks._get_user_task", return_value=completed_task),
            patch("app.api.v1.tasks.get_task_execution_mode", return_value="background"),
            patch(
                "app.api.v1.tasks.queue_task_for_background",
                side_effect=TaskExecutionStateError("Task cannot be executed from status 'completed'."),
            ),
        ):
            with self.assertRaises(HTTPException) as context:
                execute_user_task(
                    completed_task.id,
                    current_user=user,
                    db=db,
                    background_tasks=background_tasks,
                )

        self.assertEqual(context.exception.status_code, 409)

    def test_queued_status_serializes_in_task_response(self) -> None:
        task = build_task(
            status="queued",
            execution_trace=[{"step_name": "queued", "agent_name": "TaskExecutor", "status": "completed"}],
        )
        payload = _serialize_task(task)
        self.assertEqual(payload.status, "queued")

    def test_task_list_handles_queued_status(self) -> None:
        db = MagicMock()
        user = build_user()
        queued_task = build_task(user_id=user.id, status="queued")
        db.execute.return_value = FakeExecuteResult(scalar_values=[queued_task])

        tasks = list_tasks(task_status="queued", current_user=user, db=db)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].status, "queued")

    def test_task_detail_handles_queued_status(self) -> None:
        db = MagicMock()
        user = build_user()
        queued_task = build_task(user_id=user.id, status="queued")

        with patch("app.api.v1.tasks._get_user_task", return_value=queued_task):
            detail = get_task(queued_task.id, current_user=user, db=db)
            trace = get_task_trace(queued_task.id, current_user=user, db=db)

        self.assertEqual(detail.status, "queued")
        self.assertEqual(trace.status, "queued")

    def test_execution_trace_contains_queued_step_in_background_mode(self) -> None:
        db = MagicMock()
        task = build_task(status="pending")

        queued_task = queue_task_for_background(task, db)
        self.assertEqual(queued_task.status, "queued")
        self.assertEqual(queued_task.execution_trace[0]["step_name"], "queued")

    def test_background_task_uses_fresh_db_session(self) -> None:
        task = build_task(status="queued")
        fake_db = MagicMock()
        fake_db.execute.return_value = FakeExecuteResult(one=task)
        seen_dbs: list[object] = []

        def _execute_side_effect(task_arg, db_arg, **_kwargs):  # type: ignore[no-untyped-def]
            seen_dbs.append(db_arg)
            return TaskExecutionResult(task=task_arg, rag_debug=None)

        with (
            patch("app.services.task_executor.SessionLocal", return_value=fake_db),
            patch("app.services.task_executor.execute_task", side_effect=_execute_side_effect),
        ):
            run_task_execution_background(task.id, task.user_id)

        self.assertEqual(len(seen_dbs), 1)
        self.assertIs(seen_dbs[0], fake_db)
        fake_db.close.assert_called_once()

    def test_background_task_marks_processing_then_completed(self) -> None:
        db = MagicMock()
        task = build_task(
            status="queued",
            task_type="comparison",
            agent_name="ComparisonAgent",
            execution_trace=[
                {"step_name": "queued", "agent_name": "TaskExecutor", "status": "completed"}
            ],
        )
        fake_result = MagicMock()
        fake_result.final_output = "Structured comparison output."
        fake_result.execution_trace = [
            {"step_name": "classification", "agent_name": "TaskClassifier", "status": "completed"},
            {"step_name": "agent_selection", "agent_name": "ComparisonAgent", "status": "completed"},
            {"step_name": "execution", "agent_name": "ComparisonAgent", "status": "completed"},
        ]
        fake_result.rag_debug = None

        with patch("app.services.task_executor.orchestrate_task", return_value=fake_result):
            execution = execute_task(task, db)

        self.assertEqual(execution.task.status, "completed")
        self.assertGreaterEqual(len(execution.task.execution_trace), 4)
        self.assertEqual(execution.task.execution_trace[0]["step_name"], "queued")
        step_names = [step.get("step_name") for step in execution.task.execution_trace]
        self.assertIn("execution", step_names)

    def test_background_task_marks_failed_on_exception(self) -> None:
        task = build_task(
            status="queued",
            execution_trace=[{"step_name": "queued", "agent_name": "TaskExecutor", "status": "completed"}],
            started_at=datetime.now(UTC),
        )
        fake_db = MagicMock()
        fake_db.execute.return_value = FakeExecuteResult(one=task)

        with (
            patch("app.services.task_executor.SessionLocal", return_value=fake_db),
            patch(
                "app.services.task_executor.execute_task",
                side_effect=RuntimeError("failure OPENROUTER_API_KEY=sk-or-v1-secret"),
            ),
        ):
            run_task_execution_background(task.id, task.user_id)

        self.assertEqual(task.status, "failed")
        self.assertIn("sk-or-***", task.error_message or "")
        self.assertNotIn("sk-or-v1-secret", task.error_message or "")
        self.assertEqual(task.execution_trace[-1]["status"], "failed")
        fake_db.close.assert_called_once()

    def test_background_failure_error_is_sanitized(self) -> None:
        task = build_task(status="queued")
        fake_db = MagicMock()
        fake_db.execute.return_value = FakeExecuteResult(one=task)

        with (
            patch("app.services.task_executor.SessionLocal", return_value=fake_db),
            patch(
                "app.services.task_executor.execute_task",
                side_effect=RuntimeError("Authorization: Bearer top-secret sk-or-v1-real-secret"),
            ),
        ):
            run_task_execution_background(task.id, task.user_id)

        self.assertEqual(task.status, TASK_STATUS_FAILED)
        self.assertIn("Bearer ***", task.error_message or "")
        self.assertIn("sk-or-***", task.error_message or "")
        self.assertNotIn("top-secret", task.error_message or "")

    def test_task_does_not_remain_processing_on_failure(self) -> None:
        task = build_task(status="queued")
        fake_db = MagicMock()
        fake_db.execute.return_value = FakeExecuteResult(one=task)

        with (
            patch("app.services.task_executor.SessionLocal", return_value=fake_db),
            patch(
                "app.services.task_executor.execute_task",
                side_effect=RuntimeError("unexpected background error"),
            ),
        ):
            run_task_execution_background(task.id, task.user_id)

        self.assertEqual(task.status, "failed")
        self.assertNotEqual(task.status, "processing")

    def test_no_openrouter_call_in_async_tests(self) -> None:
        self.assertNotEqual(get_task_execution_mode(), "background")
        self.assertEqual(get_task_execution_mode(), "sync")


if __name__ == "__main__":
    unittest.main()
