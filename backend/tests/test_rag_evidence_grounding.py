from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.agents.prompts import build_analysis_prompt
from app.services.retrieval_service import RetrievedChunk, build_context
from app.services.task_orchestrator import _validate_output_quality, orchestrate_task
from tests.helpers import build_task


class RagEvidenceGroundingTests(unittest.TestCase):
    def test_rag_prompt_requires_evidence_section_when_context_exists(self) -> None:
        prompt = build_analysis_prompt(
            "Auditoria Aegis",
            "Analiza riesgos con evidencia",
            retrieved_context="Document: aegis_report.md\nChunk: 2\nContent:\nAegis uses pgvector.",
        )
        self.assertIn("Evidencias usadas / Evidence used", prompt)

    def test_rag_context_block_includes_document_titles(self) -> None:
        context = build_context(
            [
                RetrievedChunk(
                    chunk_id="chunk-1",
                    document_id="doc-1",
                    document_title="aegis_report.md",
                    source_name="upload/aegis_report.md",
                    chunk_index=2,
                    text="Aegis uses pgvector for semantic retrieval.",
                    score=0.82,
                )
            ]
        )
        self.assertIsNotNone(context.text)
        self.assertIn("Document: aegis_report.md", context.text or "")

    def test_rag_context_block_includes_chunk_snippets(self) -> None:
        context = build_context(
            [
                RetrievedChunk(
                    chunk_id="chunk-1",
                    document_id="doc-1",
                    document_title="aegis_report.md",
                    source_name="upload/aegis_report.md",
                    chunk_index=2,
                    text="Railway deployment and OpenRouter usage details.",
                    score=0.82,
                )
            ]
        )
        self.assertIn("Content:", context.text or "")
        self.assertIn("Railway deployment", context.text or "")

    def test_rag_quality_gate_accepts_spanish_evidence_section(self) -> None:
        task = build_task(task_type="analysis", title="Auditoria RAG", description="Revisa riesgos")
        output = (
            "Riesgos: drift de configuracion.\n"
            "Impacto: degradacion del servicio.\n"
            "Mitigacion: checklist de release.\n\n"
            "## Evidencias usadas\n"
            "1. Documento: aegis_report.md\n"
            "   Evidencia: se describe falla de despliegue.\n"
            "   Uso en el analisis: prioriza mitigaciones."
        )
        error = _validate_output_quality(task, output, rag_retrieved_chunks_count=2)
        self.assertIsNone(error, msg=error)

    def test_rag_quality_gate_rejects_rag_answer_without_evidence_when_chunks_exist(self) -> None:
        task = build_task(task_type="analysis", title="Auditoria RAG", description="Revisa riesgos")
        output = (
            "Riesgos: drift de configuracion.\n"
            "Impacto: degradacion del servicio.\n"
            "Mitigacion: checklist de release."
        )
        error = _validate_output_quality(task, output, rag_retrieved_chunks_count=2)
        self.assertEqual(
            error,
            "RAG output must include an evidence section when document chunks are retrieved.",
        )

    def test_trace_includes_rag_vector_backend(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent", title="Aegis review")
        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title="aegis_report.md",
            source_name="upload/aegis_report.md",
            chunk_index=1,
            text="Operational constraints and migration notes.",
            score=0.84,
        )
        output = (
            "Task-specific analysis and recommendation with risks impact mitigation.\n\n"
            "## Evidencias usadas / Evidence used\n"
            "1. Documento / Document: aegis_report.md\n"
            "   Evidencia: Operational constraints and migration notes.\n"
            "   Uso en el analisis: Supports release recommendation."
        )
        with (
            patch("app.services.task_orchestrator.retrieve_relevant_chunks", return_value=[chunk]),
            patch("app.services.task_orchestrator.settings.RAG_VECTOR_BACKEND", "pgvector"),
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=MagicMock(text=None, task_count=0, truncated=False),
            ),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda *_args, **_kwargs: output},
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db=MagicMock())
        retrieval_step = next(step for step in result.execution_trace if step["step_name"] == "document_retrieval")
        self.assertEqual(retrieval_step.get("rag_vector_backend"), "pgvector")

    def test_trace_includes_rag_documents_used(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent", title="Aegis review")
        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title="aegis_report.md",
            source_name="upload/aegis_report.md",
            chunk_index=1,
            text="Operational constraints and migration notes.",
            score=0.84,
        )
        output = (
            "Task-specific analysis and recommendation with risks impact mitigation.\n\n"
            "## Sources used\n"
            "1. Document: aegis_report.md\n"
            "   Evidence: migration notes\n"
            "   Use in analysis: supports recommendation."
        )
        with (
            patch("app.services.task_orchestrator.retrieve_relevant_chunks", return_value=[chunk]),
            patch("app.services.task_orchestrator.settings.RAG_VECTOR_BACKEND", "pgvector"),
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=MagicMock(text=None, task_count=0, truncated=False),
            ),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda *_args, **_kwargs: output},
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db=MagicMock())
        retrieval_step = next(step for step in result.execution_trace if step["step_name"] == "document_retrieval")
        self.assertIn("aegis_report.md", retrieval_step.get("rag_documents_used") or [])

    def test_no_openrouter_call_in_rag_evidence_tests(self) -> None:
        task = build_task(task_type="analysis", title="Auditoria RAG", description="Revisa riesgos")
        output = (
            "Risk: config drift for Auditoria RAG task.\nImpact: downtime risk in Auditoria RAG task.\nMitigation: release checklist for Auditoria RAG task.\n\n"
            "## Evidence used\n1. Document: aegis_report.md\nEvidence: deployment note.\nUse in analysis: supports mitigation."
        )
        with patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider._build_client") as build_client:
            error = _validate_output_quality(task, output, rag_retrieved_chunks_count=1)
        self.assertIsNone(error, msg=error)
        build_client.assert_not_called()

    def test_non_rag_task_does_not_require_evidence_section(self) -> None:
        task = build_task(task_type="analysis", title="Auditoria local", description="Sin docs")
        output = (
            "Risk: config drift for auditoria local task.\nImpact: downtime for auditoria local task.\nMitigation: release checklist for auditoria local task.\n"
            "Final recommendation: enforce readiness validation."
        )
        error = _validate_output_quality(task, output, rag_retrieved_chunks_count=0)
        self.assertIsNone(error, msg=error)


if __name__ == "__main__":
    unittest.main()
