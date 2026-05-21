from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from app.agents.analysis_agent import run_task as run_analysis_task
from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.comparison_agent import run_task_with_metadata as run_comparison_task_with_metadata
from app.agents.general_assistant_agent import run_task as run_general_task
from app.agents.planning_agent import run_task as run_planning_task
from app.agents.prompts import (
    build_analysis_prompt,
    build_comparison_prompt,
    build_general_prompt,
    build_planning_prompt,
    build_research_prompt,
    build_summary_prompt,
)
from app.agents.research_agent import run_task as run_research_task
from app.agents.summary_agent import run_task as run_summary_task
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
        "OPENROUTER_API_KEY": None,
        "OPENROUTER_MODEL": "openrouter/test-model",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
        "OPENROUTER_SITE_URL": "http://localhost:5173",
        "OPENROUTER_APP_NAME": "Aegis",
        "OPENAI_MODEL": "gpt-4o-mini",
        "RAG_TOP_K": 3,
        "RAG_MIN_SCORE": 0.2,
        "FULL_CONTEXT_MAX_CHARS": 3500,
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


class AgentPromptDesignTests(unittest.TestCase):
    def test_comparison_prompt_contains_required_sections(self) -> None:
        prompt = build_comparison_prompt("Compara FastAPI y Django", "Incluye ventajas y recomendación.")
        self.assertIn("Resumen ejecutivo / Executive summary", prompt)
        self.assertIn("Opciones comparadas / Compared options", prompt)
        self.assertIn("Recomendación final / Final recommendation", prompt)

    def test_analysis_prompt_contains_required_sections(self) -> None:
        prompt = build_analysis_prompt("Riesgos Railway", "Necesito impacto y mitigación.")
        self.assertIn("Executive summary / Resumen ejecutivo", prompt)
        self.assertIn("Risks / Riesgos", prompt)
        self.assertIn("Impact / Impacto", prompt)
        self.assertIn("Mitigation / Mitigacion", prompt)

    def test_planning_prompt_contains_required_sections(self) -> None:
        prompt = build_planning_prompt("Plan plataforma", "Plan paso a paso.")
        self.assertIn("Pasos detallados / Step-by-step plan", prompt)
        self.assertIn("Criterios de éxito / Success criteria", prompt)
        self.assertIn("Siguiente acción recomendada / Next recommended action", prompt)

    def test_summary_prompt_contains_required_sections(self) -> None:
        prompt = build_summary_prompt("Resume documento", "Mantén lo importante.")
        self.assertIn("Idea principal / Main idea", prompt)
        self.assertIn("Puntos clave / Key points", prompt)
        self.assertIn("Conclusión / Conclusion", prompt)

    def test_research_prompt_does_not_claim_internet_access(self) -> None:
        prompt = build_research_prompt("Research options", "Need structured findings.")
        self.assertIn("Never claim internet browsing or external source access.", prompt)
        self.assertIn("Never fabricate references or citations.", prompt)

    def test_general_prompt_does_not_contain_placeholder_language(self) -> None:
        prompt = build_general_prompt("Need help", "Give practical steps.").lower()
        self.assertNotIn("ready for future expansion", prompt)
        self.assertNotIn("general assistant workflow", prompt)
        self.assertNotIn("placeholder response", prompt)

    def test_comparison_template_fallback_is_structured(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="comparison", agent_name="ComparisonAgent", title="Compara FastAPI y Django")
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_comparison_task(task)
        self.assertIn("# Comparación técnica", output)
        self.assertIn("## 6. Recomendación final", output)

    def test_analysis_template_fallback_is_structured(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="analysis", agent_name="AnalysisAgent", title="Riesgos Railway")
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_analysis_task(task)
        self.assertIn("# Analisis tecnico", output)
        self.assertIn("## 4. Mitigation / Mitigacion", output)

    def test_planning_template_fallback_is_structured(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="planning", agent_name="PlanningAgent", title="Plan plataforma IA")
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_planning_task(task)
        self.assertIn("# Plan de ejecución", output)
        self.assertIn("## 3. Pasos detallados", output)

    def test_summary_template_fallback_is_structured(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="summary", agent_name="SummaryAgent", title="Resume informe")
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_summary_task(task)
        self.assertIn("# Resumen", output)
        self.assertIn("## 2. Puntos clave", output)

    def test_research_template_fallback_is_structured(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="research", agent_name="ResearchAgent", title="Research opciones backend")
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_research_task(task)
        self.assertIn("# Investigación estructurada", output)
        self.assertIn("No se han usado búsquedas externas", output)

    def test_general_template_fallback_is_useful(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent", title="Ayuda backend")
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_general_task(task).lower()
        self.assertIn("pasos sugeridos", output)
        self.assertTrue("siguiente acción" in output or "siguiente accion" in output)

    def test_spanish_input_preserves_spanish_prompt_instruction(self) -> None:
        prompt = build_comparison_prompt(
            "Compara FastAPI y Django",
            "Dame ventajas, desventajas y recomendación.",
        )
        self.assertIn("Language: respond in Spanish.", prompt)

    def test_english_input_preserves_english_prompt_instruction(self) -> None:
        prompt = build_comparison_prompt(
            "Compare FastAPI and Django",
            "Include trade-offs and recommendation.",
        )
        self.assertIn("Language: respond in English.", prompt)

    def test_agent_outputs_still_include_llm_metadata(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="mock"))
        task = build_task(task_type="comparison", agent_name="ComparisonAgent", title="Compare frameworks")
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            result = run_comparison_task_with_metadata(task)
        self.assertIsNotNone(result.llm_provider)
        self.assertIsNotNone(result.llm_model)
        self.assertIsNotNone(result.total_tokens)

    def test_execution_trace_still_includes_llm_metadata_after_prompt_refactor(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="comparison", agent_name="ComparisonAgent", title="Compare FastAPI and Django")
        with (
            patch("app.services.llm_service.get_llm_service", return_value=service),
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
        ):
            result = orchestrate_task(task, db=MagicMock())

        execution_steps = [s for s in result.execution_trace if s.get("step_name") == "execution"]
        self.assertTrue(execution_steps)
        self.assertIn("llm_provider", execution_steps[-1])
        self.assertIn("llm_fallback_used", execution_steps[-1])

    def test_no_placeholder_language_in_agent_fallbacks(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(
            task_type="comparison",
            agent_name="ComparisonAgent",
            title="Compara FastAPI y Django",
            description="Dame una recomendación final.",
        )
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            output = run_comparison_task(task).lower()

        forbidden = (
            "future expansion",
            "placeholder",
            "general assistant workflow",
            "not implemented",
            "todo",
            "mock response",
        )
        for phrase in forbidden:
            self.assertNotIn(phrase, output)

    def test_tests_do_not_use_openrouter_real_provider(self) -> None:
        service = LLMService(settings=_settings(LLM_PROVIDER="template"))
        task = build_task(task_type="comparison", agent_name="ComparisonAgent", title="Compare FastAPI and Django")
        with (
            patch("app.services.llm_service.get_llm_service", return_value=service),
            patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider._build_client") as build_client,
        ):
            run_comparison_task(task)

        build_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()

