from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.agents.prompts import build_analysis_fallback, build_analysis_prompt
from app.services.task_orchestrator import (
    AGENT_RUNNERS,
    OrchestrationRagDebugInfo,
    RAGContext,
    _validate_output_quality,
    orchestrate_task,
)
from tests.helpers import build_task


def _analysis_task() -> object:
    return build_task(
        task_type="analysis",
        agent_name="AnalysisAgent",
        title="Validacion RAG pgvector final",
        description=(
            "Usa los documentos subidos para auditoria tecnica de Aegis con riesgos, impacto y mitigacion."
        ),
    )


def _valid_analysis_output_en() -> str:
    return (
        "## 1. Executive summary\n"
        "The analysis reviews Aegis production posture using retrieved document context.\n\n"
        "## 2. Risks\n"
        "- Risk: release drift between migrations and runtime startup sequence.\n\n"
        "## 3. Impact\n"
        "- Impact: failed startup can pause execution pipelines and task completion.\n\n"
        "## 4. Mitigation\n"
        "- Mitigation: enforce migration checks and rollout checklist before traffic.\n\n"
        "## 5. Priority\n"
        "- High priority to reduce downtime probability.\n\n"
        "## 6. Final recommendation\n"
        "- Gate releases on readiness checks and migration success.\n\n"
        "## 7. Assumptions and limits\n"
        "- Based on currently available task and document context."
    )


def _valid_analysis_output_es() -> str:
    return (
        "## 1. Resumen ejecutivo\n"
        "La auditoria tecnica de Aegis usa el contexto documental recuperado para riesgos clave.\n\n"
        "## 2. Riesgos\n"
        "- Riesgo: desalineacion entre migraciones y arranque del backend.\n\n"
        "## 3. Impacto\n"
        "- Impacto: degradacion del servicio y retraso en ejecucion de tareas.\n\n"
        "## 4. Mitigacion\n"
        "- Mitigacion: checklist de release y validacion previa de readiness.\n\n"
        "## 5. Prioridad\n"
        "- Prioridad alta para estabilidad operativa.\n\n"
        "## 6. Recomendacion final\n"
        "- Bloquear despliegues cuando falle migracion o readiness.\n\n"
        "## 7. Supuestos y limites\n"
        "- Basado en documentos y contexto de tarea disponibles."
    )


def _rag_debug_with_chunks() -> OrchestrationRagDebugInfo:
    return OrchestrationRagDebugInfo(
        query="auditoria tecnica aegis",
        top_k=5,
        min_score=0.0,
        retrieved_chunks=[],
        memory_task_count=0,
        context_preview="chunk a\nchunk b",
        memory_context_preview=None,
        full_context_preview="chunk a\nchunk b",
        context_truncated=False,
        memory_context_truncated=False,
        full_context_truncated=False,
        retrieval_error=None,
        enabled=True,
        retrieved_chunks_count=5,
        documents_used=["aegis_phase_report.txt", "release_notes.md"],
        empty_reason=None,
        context_chars=220,
        trace_snippets=["chunk a", "chunk b"],
        vector_backend="pgvector",
    )


def _rag_context_with_chunks() -> RAGContext:
    return RAGContext(
        enabled=True,
        query="auditoria tecnica aegis",
        retrieved_chunks=[],
        retrieved_chunks_count=5,
        documents_used=["aegis_phase_report.txt", "release_notes.md"],
        empty_reason=None,
        context_text="chunk a\nchunk b",
        context_chars=220,
        snippets=["chunk a", "chunk b"],
        scores=[0.91, 0.87],
        truncated=False,
        vector_backend="pgvector",
        error=None,
    )


class AnalysisQualityGateAlignmentTests(unittest.TestCase):
    def test_analysis_quality_gate_accepts_english_sections(self) -> None:
        error = _validate_output_quality(_analysis_task(), _valid_analysis_output_en())
        self.assertIsNone(error, msg=error)

    def test_analysis_quality_gate_accepts_spanish_sections(self) -> None:
        error = _validate_output_quality(_analysis_task(), _valid_analysis_output_es())
        self.assertIsNone(error, msg=error)

    def test_analysis_quality_gate_rejects_missing_risks(self) -> None:
        output = (
            "## 1. Executive summary\n"
            "The analysis reviews Aegis production posture with document context.\n\n"
            "## 2. Findings\n"
            "- Deployment drift exists between migrations and startup sequence.\n\n"
            "## 3. Impact\n"
            "- Impact: startup failures can pause orchestration and delay delivery.\n\n"
            "## 4. Mitigation\n"
            "- Mitigation: enforce migration checks and readiness gates.\n\n"
            "## 5. Priority\n"
            "- High priority for operational continuity.\n\n"
            "## 6. Final recommendation\n"
            "- Apply release gates before opening traffic.\n\n"
            "## 7. Assumptions and limits\n"
            "- Based on the current task and document context."
        )
        error = _validate_output_quality(_analysis_task(), output)
        self.assertEqual(error, "Analysis output must include risks, impact, and mitigation.")

    def test_analysis_quality_gate_rejects_missing_impact(self) -> None:
        output = (
            "## 1. Executive summary\n"
            "The analysis reviews Aegis production posture with document context.\n\n"
            "## 2. Risks\n"
            "- Risk: deployment drift between migrations and startup sequence.\n\n"
            "## 3. Consequences\n"
            "- Service degradation may happen during rollout windows.\n\n"
            "## 4. Mitigation\n"
            "- Mitigation: enforce migration checks and readiness gates.\n\n"
            "## 5. Priority\n"
            "- High priority for operational continuity.\n\n"
            "## 6. Final recommendation\n"
            "- Apply release gates before opening traffic.\n\n"
            "## 7. Assumptions and limits\n"
            "- Based on the current task and document context."
        )
        error = _validate_output_quality(_analysis_task(), output)
        self.assertEqual(error, "Analysis output must include risks, impact, and mitigation.")

    def test_analysis_quality_gate_rejects_missing_mitigation(self) -> None:
        output = (
            "## 1. Executive summary\n"
            "The analysis reviews Aegis production posture with document context.\n\n"
            "## 2. Risks\n"
            "- Risk: deployment drift between migrations and startup sequence.\n\n"
            "## 3. Impact\n"
            "- Impact: startup failures can pause orchestration and delay delivery.\n\n"
            "## 4. Actions\n"
            "- Apply release gates and operational checks before traffic.\n\n"
            "## 5. Priority\n"
            "- High priority for operational continuity.\n\n"
            "## 6. Final recommendation\n"
            "- Apply release gates before opening traffic.\n\n"
            "## 7. Assumptions and limits\n"
            "- Based on the current task and document context."
        )
        error = _validate_output_quality(_analysis_task(), output)
        self.assertEqual(error, "Analysis output must include risks, impact, and mitigation.")

    def test_analysis_agent_prompt_requires_bilingual_required_sections(self) -> None:
        prompt = build_analysis_prompt(
            "Validacion RAG pgvector final",
            "Necesito analisis con riesgos, impacto y mitigacion.",
            retrieved_context="Chunk 1\nChunk 2",
        )
        self.assertIn("Executive summary / Resumen ejecutivo", prompt)
        self.assertIn("Risks / Riesgos", prompt)
        self.assertIn("Impact / Impacto", prompt)
        self.assertIn("Mitigation / Mitigacion", prompt)
        self.assertIn("Priority / Prioridad", prompt)
        self.assertIn("Final recommendation / Recomendacion final", prompt)
        self.assertIn("Assumptions and limits / Supuestos y limites", prompt)

    def test_analysis_agent_fallback_contains_required_sections(self) -> None:
        output = build_analysis_fallback(
            "Validacion RAG pgvector final",
            "Contexto documental de auditoria tecnica.",
        )
        self.assertIn("## 1. Executive summary / Resumen ejecutivo", output)
        self.assertIn("## 2. Risks / Riesgos", output)
        self.assertIn("## 3. Impact / Impacto", output)
        self.assertIn("## 4. Mitigation / Mitigacion", output)

    def test_rag_analysis_output_with_spanish_headings_passes_quality_gate(self) -> None:
        output = _valid_analysis_output_es() + "\n\nSegun el contexto documental disponible."
        error = _validate_output_quality(_analysis_task(), output)
        self.assertIsNone(error, msg=error)

    def test_analysis_output_does_not_fail_when_rag_retrieved_chunks_exist(self) -> None:
        task = _analysis_task()
        rag_debug = _rag_debug_with_chunks()
        rag_context = _rag_context_with_chunks()
        result_output = (
            f"{_valid_analysis_output_es()}\n\n"
            "## Evidencias usadas / Evidence used\n"
            "1. Documento / Document: aegis_phase_report.txt\n"
            "   Evidencia: chunk de riesgos operativos.\n"
            "   Uso en el analisis: sustenta la recomendacion final."
        )

        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=("chunk a\nchunk b", rag_debug, rag_context)),
            patch.dict(AGENT_RUNNERS, {"AnalysisAgent": lambda *_args, **_kwargs: result_output}, clear=False),
        ):
            result = orchestrate_task(task, db=MagicMock())

        self.assertEqual(result.final_output, result_output)
        failed_steps = [step for step in result.execution_trace if step.get("status") == "failed"]
        self.assertEqual(failed_steps, [])
        retrieval_steps = [step for step in result.execution_trace if step.get("step_name") == "document_retrieval"]
        self.assertTrue(retrieval_steps)
        self.assertEqual(retrieval_steps[0].get("rag_retrieved_chunks_count"), 5)

    def test_quality_gate_does_not_call_openrouter(self) -> None:
        with patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider._build_client") as build_client:
            error = _validate_output_quality(_analysis_task(), _valid_analysis_output_es())
        self.assertIsNone(error, msg=error)
        build_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
