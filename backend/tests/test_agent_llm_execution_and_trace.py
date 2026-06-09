from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from app.agents.analysis_agent import run_task as run_analysis_task
from app.agents.analysis_agent import run_task_with_metadata as run_analysis_task_with_metadata
from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.comparison_agent import run_task_with_metadata as run_comparison_task_with_metadata
from app.agents.planning_agent import run_task as run_planning_task
from app.agents.planning_agent import run_task_with_metadata as run_planning_task_with_metadata
from app.api.v1.tasks import _normalize_trace_step, _serialize_task
from app.schemas.task import TaskExecutionStepRead
from app.services.llm.service import LLMService
from app.services.llm.schemas import LLMRequest
from app.services.task_orchestrator import (
    FORBIDDEN_PLACEHOLDER_PHRASES,
    OrchestrationRagDebugInfo,
    _validate_output_quality,
    orchestrate_task,
)
from tests.helpers import build_task


def _settings(**overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "LLM_PROVIDER": "template",
        "LLM_ENABLE_REAL_CALLS": False,
        "LLM_TIMEOUT_SECONDS": 30,
        "LLM_MAX_TOKENS": 1200,
        "LLM_TEMPERATURE": 0.3,
        "OPENROUTER_API_KEY": None,
        "OPENROUTER_MODEL": "openrouter/test-model",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
        "OPENROUTER_SITE_URL": "http://localhost:5173",
        "OPENROUTER_APP_NAME": "Aegis",
        "OPENAI_MODEL": "gpt-5-mini",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


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


class AgentLLMExecutionAndTraceTests(unittest.TestCase):
    def test_comparison_agent_returns_llm_metadata_with_mock_provider(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="mock"))
        task = build_task(task_type="comparison", agent_name="ComparisonAgent", title="Compara FastAPI y Django")

        with patch("app.services.llm_service.get_llm_service", return_value=service):
            result = run_comparison_task_with_metadata(task)

        self.assertEqual(result.llm_provider, "mock")
        self.assertIsNotNone(result.llm_model)
        self.assertIsNotNone(result.total_tokens)

    def test_analysis_agent_returns_llm_metadata_with_mock_provider(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="mock"))
        task = build_task(task_type="analysis", agent_name="AnalysisAgent", title="Riesgos Railway")

        with patch("app.services.llm_service.get_llm_service", return_value=service):
            result = run_analysis_task_with_metadata(task)

        self.assertEqual(result.llm_provider, "mock")
        self.assertIsNotNone(result.llm_model)
        self.assertIsNotNone(result.total_tokens)

    def test_planning_agent_returns_llm_metadata_with_mock_provider(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="mock"))
        task = build_task(task_type="planning", agent_name="PlanningAgent", title="Plan plataforma agentes")

        with patch("app.services.llm_service.get_llm_service", return_value=service):
            result = run_planning_task_with_metadata(task)

        self.assertEqual(result.llm_provider, "mock")
        self.assertIsNotNone(result.llm_model)
        self.assertIsNotNone(result.total_tokens)

    def test_comparison_agent_template_fallback_still_contains_required_sections(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="comparison", agent_name="ComparisonAgent", title="Compara FastAPI y Django")

        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_comparison_task(task).lower()

        self.assertIn("executive summary", output)
        self.assertTrue("advantages / pros" in output or "advantages" in output)
        self.assertIn("final recommendation", output)

    def test_analysis_agent_template_fallback_still_contains_risks_impact_mitigation(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="analysis", agent_name="AnalysisAgent", title="Riesgos Railway")

        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_analysis_task(task).lower()

        self.assertIn("risks / riesgos", output)
        self.assertIn("impact", output)
        self.assertIn("mitigation", output)

    def test_planning_agent_template_fallback_still_contains_steps_and_next_action(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="planning", agent_name="PlanningAgent", title="Plan plataforma agentes")

        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_planning_task(task).lower()

        self.assertIn("step-by-step plan", output)
        self.assertIn("1.", output)
        self.assertIn("next action", output)

    def test_execution_trace_includes_llm_metadata_for_comparison_agent(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="comparison", agent_name="ComparisonAgent")

        with (
            patch("app.services.llm_service.get_llm_service", return_value=service),
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
        ):
            result = orchestrate_task(task, db=MagicMock())

        comparison_steps = [
            s
            for s in result.execution_trace
            if s.get("agent_name") == "ComparisonAgent" and s.get("step_name") == "execution"
        ]
        self.assertTrue(comparison_steps)
        self.assertEqual(comparison_steps[0].get("llm_provider"), "template")

    def test_execution_trace_includes_llm_metadata_for_analysis_agent(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="analysis", agent_name="AnalysisAgent")

        with (
            patch("app.services.llm_service.get_llm_service", return_value=service),
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
        ):
            result = orchestrate_task(task, db=MagicMock())

        analysis_steps = [
            s
            for s in result.execution_trace
            if s.get("agent_name") == "AnalysisAgent" and s.get("step_name") == "execution"
        ]
        self.assertTrue(analysis_steps)
        self.assertEqual(analysis_steps[0].get("llm_provider"), "template")

    def test_execution_trace_includes_llm_metadata_for_planning_agent(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="planning", agent_name="PlanningAgent")

        with (
            patch("app.services.llm_service.get_llm_service", return_value=service),
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
        ):
            result = orchestrate_task(task, db=MagicMock())

        planning_steps = [
            s
            for s in result.execution_trace
            if s.get("agent_name") == "PlanningAgent" and s.get("step_name") == "execution"
        ]
        self.assertTrue(planning_steps)
        self.assertEqual(planning_steps[0].get("llm_provider"), "template")

    def test_openrouter_disabled_does_not_call_external_api_in_agent_execution(self) -> None:
        service = LLMService(
            settings=_settings(
                LLM_PROVIDER="openrouter",
                LLM_ENABLE_REAL_CALLS=False,
                OPENROUTER_API_KEY="dummy-key",
            )
        )
        task = build_task(task_type="comparison", agent_name="ComparisonAgent")

        with (
            patch("app.services.llm_service.get_llm_service", return_value=service),
            patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider._build_client") as build_client,
        ):
            result = run_comparison_task_with_metadata(task)

        build_client.assert_not_called()
        self.assertEqual(result.llm_provider, "openrouter")
        self.assertTrue(result.fallback_used)

    def test_agent_output_quality_gate_rejects_placeholder_after_llm_integration(self) -> None:
        task = build_task(task_type="general", title="General support request")
        output = (
            "This response is intentionally long enough to pass minimum checks, but it includes "
            "future expansion wording and should be rejected by the quality gate."
        )
        error = _validate_output_quality(task, output)
        self.assertIsNotNone(error)
        self.assertIn("disallowed placeholder language", error or "")

    def test_legacy_trace_compatibility_after_llm_metadata_added(self) -> None:
        legacy_trace = {"step": "execution", "summary": "Legacy item still valid"}
        normalized = _normalize_trace_step(legacy_trace, "ComparisonAgent")
        model = TaskExecutionStepRead.model_validate(normalized)
        self.assertEqual(model.step_name, "execution")
        self.assertEqual(model.agent_name, "ComparisonAgent")
        self.assertIsNone(model.llm_provider)

    def test_task_detail_contract_still_contains_result_trace_agent_type(self) -> None:
        task = build_task(
            status="completed",
            task_type="comparison",
            agent_name="ComparisonAgent",
            result_text="Structured comparison result.",
            execution_trace=[
                {"step_name": "classification", "agent_name": "TaskClassifier", "status": "completed"},
                {
                    "step_name": "execution",
                    "agent_name": "ComparisonAgent",
                    "status": "completed",
                    "llm_provider": "template",
                },
            ],
        )
        payload = _serialize_task(task).model_dump()
        self.assertIn("result_text", payload)
        self.assertIn("execution_trace", payload)
        self.assertEqual(payload["agent_name"], "ComparisonAgent")

    def test_no_openrouter_api_key_is_required_for_template_mode(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template", OPENROUTER_API_KEY=None))
        response = service.generate(LLMRequest(prompt="hola"), fallback_text="template ok")
        self.assertEqual(response.provider, "template")
        self.assertEqual(response.text, "template ok")

    def test_no_real_llm_calls_are_made_in_test_suite(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="analysis", agent_name="AnalysisAgent")

        with (
            patch("app.services.llm_service.get_llm_service", return_value=service),
            patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider._build_client") as build_client,
        ):
            run_analysis_task_with_metadata(task)

        build_client.assert_not_called()


for index, phrase in enumerate(FORBIDDEN_PLACEHOLDER_PHRASES, start=1):
    def _builder(forbidden_phrase: str) -> callable:
        def _test(self: AgentLLMExecutionAndTraceTests) -> None:
            task = build_task(task_type="general", title="General support request")
            output = (
                "This response contains task-relevant content but also includes forbidden language: "
                f"{forbidden_phrase}. The quality gate must reject it."
            )
            error = _validate_output_quality(task, output)
            self.assertIsNotNone(error)

        return _test

    setattr(
        AgentLLMExecutionAndTraceTests,
        f"test_quality_gate_blocks_forbidden_phrase_{index:02d}",
        _builder(phrase),
    )


if __name__ == "__main__":
    unittest.main()
