from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.agents.analysis_agent import run_task as run_analysis_task
from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.planning_agent import run_task as run_planning_task
from app.api.v1.health import health_check
from app.api.v1.tasks import _get_user_task, _normalize_trace_step, _serialize_task
from app.schemas.task import TaskExecutionStepRead
from app.services.agent_selector import select_agent
from app.services.task_executor import TaskExecutionError, execute_task
from app.services.task_orchestrator import (
    FORBIDDEN_PLACEHOLDER_PHRASES,
    OrchestrationRagDebugInfo,
    TaskOrchestrationError,
    _validate_output_quality,
    orchestrate_task,
)
from tests.helpers import FakeExecuteResult, build_task, build_user


def _empty_rag_debug() -> OrchestrationRagDebugInfo:
    return OrchestrationRagDebugInfo(
        query="",
        top_k=3,
        min_score=0.2,
        retrieved_chunks=[],
        memory_task_count=0,
        context_preview=None,
        memory_context_preview=None,
        full_context_preview=None,
        context_truncated=False,
        memory_context_truncated=False,
        full_context_truncated=False,
        retrieval_error=None,
    )


class PipelineRegressionQualityTests(unittest.TestCase):
    def test_health_endpoint_returns_ok_payload(self) -> None:
        payload = health_check()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "aegis-backend")

    def test_planning_task_selects_planning_agent(self) -> None:
        self.assertEqual(select_agent("planning"), "PlanningAgent")

    def test_analysis_task_selects_analysis_agent(self) -> None:
        self.assertEqual(select_agent("analysis"), "AnalysisAgent")

    def test_analysis_agent_output_contains_risks_impact_and_mitigation(self) -> None:
        task = build_task(
            task_type="analysis",
            agent_name="AnalysisAgent",
            title="Riesgos Railway",
            description="Analiza riesgos, impacto y mitigacion para despliegue backend.",
        )
        output = run_analysis_task(task).lower()
        self.assertIn("risk", output)
        self.assertIn("impact", output)
        self.assertIn("mitigation", output)

    def test_comparison_agent_output_contains_fastapi_django_and_recommendation(self) -> None:
        task = build_task(
            task_type="comparison",
            agent_name="ComparisonAgent",
            title="FastAPI vs Django comparison",
            description="Include advantages disadvantages and recommendation.",
        )
        output = run_comparison_task(task).lower()
        self.assertIn("fastapi", output)
        self.assertIn("django", output)
        self.assertTrue("advantages" in output or "pros" in output)
        self.assertTrue("disadvantages" in output or "cons" in output)
        self.assertIn("recommend", output)

    def test_planning_agent_output_contains_numbered_steps_and_next_action(self) -> None:
        task = build_task(
            task_type="planning",
            agent_name="PlanningAgent",
            title="Plan plataforma de agentes IA",
            description="Crea plan paso a paso con siguiente accion.",
        )
        output = run_planning_task(task).lower()
        self.assertIn("1.", output)
        self.assertIn("next action", output)

    def test_execution_trace_contains_classification_agent_selection_and_execution(self) -> None:
        task = build_task(
            task_type="planning",
            agent_name="PlanningAgent",
            title="Plan plataforma agentes",
            description="Crea un plan paso a paso para esta plataforma.",
        )

        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"PlanningAgent": lambda *_args, **_kwargs: run_planning_task(task)},
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db=MagicMock())

        step_names = [step["step_name"] for step in result.execution_trace]
        self.assertIn("classification", step_names)
        self.assertIn("agent_selection", step_names)
        self.assertIn("execution", step_names)

    def test_completed_task_never_contains_placeholder_language(self) -> None:
        task = build_task(
            task_type="comparison",
            agent_name="ComparisonAgent",
            title="Compara FastAPI y Django",
            description="Dame recomendacion final.",
        )
        output = run_comparison_task(task)
        lowered = output.lower()
        for phrase in FORBIDDEN_PLACEHOLDER_PHRASES:
            self.assertNotIn(phrase, lowered)

    def test_legacy_execution_trace_is_normalized_in_task_detail(self) -> None:
        legacy_trace = [
            {"step": "classification", "summary": "Clasificada correctamente"},
            {"step": "execution", "summary": "Ejecutada sin errores"},
        ]
        task = build_task(
            status="completed",
            task_type="comparison",
            agent_name="ComparisonAgent",
            execution_trace=legacy_trace,
        )

        serialized = _serialize_task(task)
        self.assertEqual(len(serialized.execution_trace), 2)
        for step in serialized.execution_trace:
            self.assertIsNotNone(step.step_name)
            self.assertIsNotNone(step.agent_name)
            self.assertIsNotNone(step.status)

    def test_task_detail_contract_contains_required_fields(self) -> None:
        task = build_task(
            status="completed",
            task_type="analysis",
            agent_name="AnalysisAgent",
            result_text="Risk analysis with mitigation and recommendation.",
            execution_trace=[
                {"step_name": "classification", "agent_name": "TaskClassifier", "status": "completed"},
                {"step_name": "agent_selection", "agent_name": "AnalysisAgent", "status": "completed"},
                {"step_name": "execution", "agent_name": "AnalysisAgent", "status": "completed"},
            ],
        )

        serialized = _serialize_task(task)
        payload = serialized.model_dump()
        required_fields = {
            "id",
            "user_id",
            "title",
            "description",
            "status",
            "task_type",
            "agent_name",
            "result_text",
            "execution_trace",
            "created_at",
            "updated_at",
        }
        self.assertTrue(required_fields.issubset(payload.keys()))
        self.assertIsInstance(payload["execution_trace"], list)

    def test_user_cannot_read_another_user_task(self) -> None:
        db = MagicMock()
        db.execute.return_value = FakeExecuteResult(one=None)
        current_user = build_user()

        with self.assertRaises(HTTPException) as context:
            _get_user_task(build_task().id, current_user, db)

        self.assertEqual(context.exception.status_code, 404)

    def test_execute_task_sets_failed_status_when_orchestration_raises(self) -> None:
        db = MagicMock()
        task = build_task(status="pending", task_type="analysis", agent_name="AnalysisAgent")

        orchestrator_error = TaskOrchestrationError(
            "Orchestration exploded",
            execution_trace=[
                {"step_name": "execution", "agent_name": "AnalysisAgent", "status": "failed"},
            ],
            rag_debug=_empty_rag_debug(),
        )

        with patch("app.services.task_executor.orchestrate_task", side_effect=orchestrator_error):
            with self.assertRaises(TaskExecutionError):
                execute_task(task, db)

        self.assertEqual(task.status, "failed")
        self.assertIsNotNone(task.started_at)
        self.assertIsNotNone(task.finished_at)
        self.assertIsNotNone(task.duration_ms)

    def test_execute_task_sets_completed_status_when_orchestration_succeeds(self) -> None:
        db = MagicMock()
        task = build_task(
            status="pending",
            task_type="comparison",
            agent_name="ComparisonAgent",
            title="Compare FastAPI and Django",
            description="Include recommendation and tradeoffs",
        )
        fake_result = MagicMock()
        fake_result.final_output = (
            "FastAPI vs Django recommendation: FastAPI for API-first speed, Django for admin-heavy needs."
        )
        fake_result.execution_trace = [
            {"step_name": "classification", "agent_name": "TaskClassifier", "status": "completed"},
            {"step_name": "agent_selection", "agent_name": "ComparisonAgent", "status": "completed"},
            {"step_name": "execution", "agent_name": "ComparisonAgent", "status": "completed"},
        ]
        fake_result.rag_debug = _empty_rag_debug()

        with patch("app.services.task_executor.orchestrate_task", return_value=fake_result):
            execution = execute_task(task, db)

        self.assertEqual(execution.task.status, "completed")
        self.assertIsNotNone(execution.task.result_text)
        self.assertIsNotNone(execution.task.started_at)
        self.assertIsNotNone(execution.task.finished_at)
        self.assertIsNotNone(execution.task.duration_ms)

    def test_trace_normalization_accepts_non_dict_legacy_items(self) -> None:
        normalized = _normalize_trace_step("legacy free text trace", "GeneralAssistantAgent")
        model = TaskExecutionStepRead.model_validate(normalized)
        self.assertEqual(model.step_name, "execution")
        self.assertEqual(model.agent_name, "GeneralAssistantAgent")


def _build_placeholder_quality_gate_test(phrase: str) -> callable:
    def _test(self: PipelineRegressionQualityTests) -> None:
        task = build_task(task_type="general", title="General support request")
        output = (
            "This output is intentionally long enough to pass minimum length checks while "
            f"still containing forbidden content: {phrase}. "
            "It also repeats task context so token checks pass for general support."
        )
        error = _validate_output_quality(task, output)
        self.assertIsNotNone(error)
        self.assertIn("disallowed placeholder language", error or "")

    return _test


for index, placeholder_phrase in enumerate(FORBIDDEN_PLACEHOLDER_PHRASES, start=1):
    method_name = (
        "test_quality_gate_rejects_placeholder_phrase_"
        f"{index:02d}_{placeholder_phrase.replace(' ', '_')}"
    )
    setattr(
        PipelineRegressionQualityTests,
        method_name,
        _build_placeholder_quality_gate_test(placeholder_phrase),
    )


QUALITY_VALID_CASES: list[tuple[str, str, str, str]] = [
    (
        "comparison",
        "Compare FastAPI and Django",
        "Need recommendation with pros and cons",
        (
            "FastAPI and Django both solve backend needs. Advantages and disadvantages were reviewed, "
            "and recommendation is FastAPI for API-first speed with Django for admin-heavy systems."
        ),
    ),
    (
        "analysis",
        "Analyze Railway risks",
        "Need impact and mitigation",
        (
            "Risk: misconfiguration during deployment. Impact: service downtime and slower recovery. "
            "Mitigation: staged rollout, monitoring, and rollback procedures."
        ),
    ),
    (
        "planning",
        "Create implementation plan",
        "Need next action",
        (
            "1. Define scope and acceptance criteria. 2. Build smallest vertical slice. "
            "3. Validate with regression checks and share the next action with stakeholders."
        ),
    ),
]


def _build_quality_positive_test(
    task_type: str,
    title: str,
    description: str,
    output: str,
) -> callable:
    def _test(self: PipelineRegressionQualityTests) -> None:
        task = build_task(task_type=task_type, title=title, description=description)
        error = _validate_output_quality(task, output)
        self.assertIsNone(error, msg=error)

    return _test


for index, (task_type, title, description, output) in enumerate(QUALITY_VALID_CASES, start=1):
    method_name = f"test_quality_gate_accepts_valid_output_case_{index:02d}_{task_type}"
    setattr(
        PipelineRegressionQualityTests,
        method_name,
        _build_quality_positive_test(task_type, title, description, output),
    )


if __name__ == "__main__":
    unittest.main()
