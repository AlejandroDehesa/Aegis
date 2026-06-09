from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from app.agents.analysis_agent import run_task as run_analysis_task
from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.execution_result import AgentExecutionResult
from app.agents.planning_agent import run_task as run_planning_task
from app.services.llm.providers.base import LLMProvider, LLMProviderError
from app.services.llm.schemas import LLMRequest, LLMResponse
from app.services.llm.service import LLMService
from app.services.task_orchestrator import OrchestrationRagDebugInfo, orchestrate_task
from tests.helpers import build_task


def _settings(**overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "LLM_PROVIDER": "template",
        "LLM_ENABLE_REAL_CALLS": False,
        "LLM_TIMEOUT_SECONDS": 30,
        "LLM_MAX_TOKENS": 1200,
        "LLM_TEMPERATURE": 0.3,
        "LLM_RETRY_ATTEMPTS": 1,
        "LLM_RETRY_BACKOFF_SECONDS": 0.01,
        "LLM_REQUEST_HARD_MAX_TOKENS": 2000,
        "LLM_TASK_TOTAL_TOKEN_SOFT_LIMIT": 6000,
        "LLM_TASK_TOTAL_TOKEN_HARD_LIMIT": 10000,
        "LLM_ENABLE_COST_ESTIMATION": True,
        "LLM_COST_PER_1M_INPUT_TOKENS": None,
        "LLM_COST_PER_1M_OUTPUT_TOKENS": None,
        "OPENROUTER_API_KEY": None,
        "OPENROUTER_MODEL": "openrouter/test-model",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
        "OPENROUTER_SITE_URL": "http://localhost:5173",
        "OPENROUTER_APP_NAME": "Aegis",
        "OPENAI_MODEL": "gpt-5-mini",
        "RAG_TOP_K": 3,
        "RAG_MIN_SCORE": 0.2,
        "FULL_CONTEXT_MAX_CHARS": 2600,
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


class _CaptureProvider(LLMProvider):
    def __init__(self) -> None:
        self.last_request: LLMRequest | None = None

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.last_request = request
        return LLMResponse(
            text="Captured request with useful Test task context and concrete recommendation.",
            provider="mock",
            model="capture-model",
        )


class _ConfigurationErrorProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        raise LLMProviderError("invalid api key format", configuration=True)


class _TransientFailThenSuccessProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        if self.calls == 1:
            raise LLMProviderError("gateway timeout", transient=True, status_code=504)
        return LLMResponse(
            text="Successful response after retry with Test task recommendation and useful details.",
            provider="openrouter",
            model="openrouter/test-model",
            prompt_tokens=100,
            completion_tokens=80,
            total_tokens=180,
        )


class _AlwaysFailProvider(LLMProvider):
    def __init__(self, message: str = "temporary backend error") -> None:
        self.calls = 0
        self.message = message

    def generate(self, request: LLMRequest) -> LLMResponse:
        self.calls += 1
        raise LLMProviderError(self.message, transient=True, status_code=503)


class _TokenProvider(LLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            text="Token provider response for Test task with practical recommendation and clear scope.",
            provider="openrouter",
            model="openrouter/test-model",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            estimated_cost=None,
        )


def _build_trace_ready_result(**overrides: object) -> AgentExecutionResult:
    payload = {
        "text": (
            "This Test task response is intentionally detailed, practical, and directly tied to the "
            "task context so the quality gate accepts it as useful output."
        ),
        "llm_provider": "openrouter",
        "llm_model": "openrouter/test-model",
        "prompt_tokens": 120,
        "completion_tokens": 80,
        "total_tokens": 200,
        "estimated_cost": None,
        "fallback_used": False,
        "llm_error": None,
        "llm_retry_count": 0,
        "llm_latency_ms": 42,
    }
    payload.update(overrides)
    return AgentExecutionResult(**payload)


class LLMLimitsAndObservabilityTests(unittest.TestCase):
    def test_llm_service_caps_max_tokens_to_hard_limit(self) -> None:
        provider = _CaptureProvider()
        service = LLMService(
            settings=_settings(LLM_PROVIDER="mock", LLM_REQUEST_HARD_MAX_TOKENS=300),
            provider_overrides={"mock": provider},
        )

        service.generate(LLMRequest(prompt="hello", max_tokens=9000))
        self.assertIsNotNone(provider.last_request)
        self.assertEqual(provider.last_request.max_tokens, 300)

    def test_llm_service_rejects_invalid_temperature(self) -> None:
        service = LLMService(settings=_settings(LLM_TEMPERATURE=2.5))
        with self.assertRaises(LLMProviderError):
            service.generate(LLMRequest(prompt="hello"))

    def test_llm_service_rejects_invalid_provider(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="invalid-provider"))
        with self.assertRaises(LLMProviderError):
            service.generate(LLMRequest(prompt="hello"))

    def test_llm_service_does_not_retry_configuration_errors(self) -> None:
        provider = _ConfigurationErrorProvider()
        service = LLMService(
            settings=_settings(LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="dummy-key"),
            provider_overrides={"openrouter": provider},
        )
        response = service.generate(LLMRequest(prompt="hello"), fallback_text="fallback text")
        self.assertTrue(response.fallback_used)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(response.retry_count, 0)

    def test_llm_service_retries_transient_provider_error_once(self) -> None:
        provider = _TransientFailThenSuccessProvider()
        service = LLMService(
            settings=_settings(LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="dummy-key", LLM_RETRY_ATTEMPTS=1),
            provider_overrides={"openrouter": provider},
        )
        with patch("app.services.llm.service.time.sleep") as sleep_mock:
            response = service.generate(LLMRequest(prompt="hello"))

        self.assertEqual(provider.calls, 2)
        self.assertEqual(response.retry_count, 1)
        sleep_mock.assert_called_once()

    def test_llm_service_falls_back_after_openrouter_failure(self) -> None:
        provider = _AlwaysFailProvider()
        service = LLMService(
            settings=_settings(LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="dummy-key", LLM_RETRY_ATTEMPTS=1),
            provider_overrides={"openrouter": provider},
        )
        response = service.generate(LLMRequest(prompt="hello"), fallback_text="fallback path")
        self.assertTrue(response.fallback_used)
        self.assertEqual(response.provider, "openrouter")
        self.assertEqual(response.text, "fallback path")
        self.assertEqual(response.retry_count, 1)
        self.assertIn("effective_provider", response.raw or {})

    def test_fallback_error_is_sanitized(self) -> None:
        provider = _AlwaysFailProvider(
            "request failed with key sk-or-v1-123456 and Authorization: Bearer secret-token"
        )
        service = LLMService(
            settings=_settings(LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="sk-or-v1-123456"),
            provider_overrides={"openrouter": provider},
        )
        response = service.generate(LLMRequest(prompt="hello"), fallback_text="fallback path")
        self.assertNotIn("sk-or-v1-123456", response.error or "")
        self.assertNotIn("secret-token", response.error or "")
        self.assertIn("sk-or-***", response.error or "")

    def test_execution_trace_records_llm_retry_count(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent")
        result_payload = _build_trace_ready_result(llm_retry_count=1)

        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda *_args, **_kwargs: result_payload},
                clear=False,
            ),
        ):
            orchestration = orchestrate_task(task, db=MagicMock())

        execution_step = [s for s in orchestration.execution_trace if s.get("step_name") == "execution"][0]
        self.assertEqual(execution_step.get("llm_retry_count"), 1)

    def test_execution_trace_records_llm_error_on_fallback(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent")
        result_payload = _build_trace_ready_result(
            fallback_used=True,
            llm_error="OpenRouter request failed: gateway timeout",
        )
        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda *_args, **_kwargs: result_payload},
                clear=False,
            ),
        ):
            orchestration = orchestrate_task(task, db=MagicMock())

        execution_step = [s for s in orchestration.execution_trace if s.get("step_name") == "execution"][0]
        self.assertTrue(execution_step.get("llm_fallback_used"))
        self.assertEqual(execution_step.get("llm_error"), "OpenRouter request failed: gateway timeout")

    def test_execution_trace_records_llm_latency_if_available(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent")
        result_payload = _build_trace_ready_result(llm_latency_ms=123)
        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda *_args, **_kwargs: result_payload},
                clear=False,
            ),
        ):
            orchestration = orchestrate_task(task, db=MagicMock())

        execution_step = [s for s in orchestration.execution_trace if s.get("step_name") == "execution"][0]
        self.assertEqual(execution_step.get("llm_latency_ms"), 123)

    def test_task_llm_usage_summary_counts_tokens(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent")
        result_payload = _build_trace_ready_result(prompt_tokens=300, completion_tokens=200, total_tokens=500)
        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda *_args, **_kwargs: result_payload},
                clear=False,
            ),
        ):
            orchestration = orchestrate_task(task, db=MagicMock())

        summary_step = [s for s in orchestration.execution_trace if s.get("step_name") == "llm_usage_summary"][0]
        usage = summary_step.get("llm_usage_summary") or {}
        self.assertEqual(usage.get("total_prompt_tokens"), 300)
        self.assertEqual(usage.get("total_completion_tokens"), 200)
        self.assertEqual(usage.get("total_tokens"), 500)

    def test_task_llm_usage_summary_marks_fallback_used_any(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent")
        result_payload = _build_trace_ready_result(fallback_used=True)
        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda *_args, **_kwargs: result_payload},
                clear=False,
            ),
        ):
            orchestration = orchestrate_task(task, db=MagicMock())

        usage = [s for s in orchestration.execution_trace if s.get("step_name") == "llm_usage_summary"][0][
            "llm_usage_summary"
        ]
        self.assertTrue(usage.get("fallback_used_any"))

    def test_task_llm_usage_summary_counts_errors(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent")
        result_payload = _build_trace_ready_result(
            fallback_used=True,
            llm_error="sanitized llm error",
        )
        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda *_args, **_kwargs: result_payload},
                clear=False,
            ),
        ):
            orchestration = orchestrate_task(task, db=MagicMock())

        usage = [s for s in orchestration.execution_trace if s.get("step_name") == "llm_usage_summary"][0][
            "llm_usage_summary"
        ]
        self.assertEqual(usage.get("llm_errors_count"), 1)

    def test_estimated_cost_is_null_without_prices(self) -> None:
        service = LLMService(
            settings=_settings(
                LLM_PROVIDER="openrouter",
                OPENROUTER_API_KEY="dummy-key",
                LLM_COST_PER_1M_INPUT_TOKENS=None,
                LLM_COST_PER_1M_OUTPUT_TOKENS=None,
            ),
            provider_overrides={"openrouter": _TokenProvider()},
        )
        response = service.generate(LLMRequest(prompt="hello"))
        self.assertIsNone(response.estimated_cost)

    def test_estimated_cost_uses_configured_prices_when_available(self) -> None:
        service = LLMService(
            settings=_settings(
                LLM_PROVIDER="openrouter",
                OPENROUTER_API_KEY="dummy-key",
                LLM_COST_PER_1M_INPUT_TOKENS=1.0,
                LLM_COST_PER_1M_OUTPUT_TOKENS=2.0,
            ),
            provider_overrides={"openrouter": _TokenProvider()},
        )
        response = service.generate(LLMRequest(prompt="hello"))
        self.assertIsNotNone(response.estimated_cost)
        self.assertAlmostEqual(response.estimated_cost or 0.0, 0.002, places=8)

    def test_no_api_key_in_error_messages(self) -> None:
        provider = _AlwaysFailProvider("failure with OPENROUTER_API_KEY=sk-or-v1-secretvalue")
        service = LLMService(
            settings=_settings(LLM_PROVIDER="openrouter", OPENROUTER_API_KEY="sk-or-v1-secretvalue"),
            provider_overrides={"openrouter": provider},
        )
        response = service.generate(LLMRequest(prompt="hello"), fallback_text="fallback text")
        self.assertNotIn("secretvalue", response.error or "")
        self.assertIn("sk-or-***", response.error or "")

    def test_no_real_openrouter_calls_in_cost_control_tests(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        with patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider._build_client") as build_client:
            service.generate(LLMRequest(prompt="hello"), fallback_text="fallback text")
        build_client.assert_not_called()

    def test_existing_comparison_analysis_planning_flows_still_pass(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        comparison_task = build_task(task_type="comparison", agent_name="ComparisonAgent", title="Compare FastAPI")
        analysis_task = build_task(task_type="analysis", agent_name="AnalysisAgent", title="Analyze risks")
        planning_task = build_task(task_type="planning", agent_name="PlanningAgent", title="Plan release")

        with patch("app.services.llm_service.get_llm_service", return_value=service):
            comparison_output = run_comparison_task(comparison_task).lower()
            analysis_output = run_analysis_task(analysis_task).lower()
            planning_output = run_planning_task(planning_task).lower()

        self.assertIn("recommend", comparison_output)
        self.assertIn("risk", analysis_output)
        self.assertIn("next action", planning_output)


if __name__ == "__main__":
    unittest.main()
