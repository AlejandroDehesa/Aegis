from __future__ import annotations

from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import MagicMock, patch

from app.agents.analysis_agent import run_task as run_analysis_task
from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.execution_result import AgentExecutionResult
from app.agents.planning_agent import run_task as run_planning_task
from app.agents.prompts import (
    build_analysis_prompt,
    build_comparison_prompt,
    build_planning_prompt,
    build_research_prompt,
    build_summary_prompt,
)
from app.api.v1.tasks import _serialize_task
from app.services.document_service import _chunk_text
from app.services.llm.service import LLMService
from app.services.memory_service import MemoryContextResult
from app.services.retrieval_service import RetrievedChunk, build_context, retrieve_relevant_chunks
from app.services.task_orchestrator import _prepare_combined_context, orchestrate_task
from tests.helpers import build_task


def _long_valid_output(task_title: str) -> str:
    return (
        f"This response addresses {task_title} with concrete implementation guidance, practical next actions, "
        "explicit assumptions, and enough task-specific detail to satisfy the output quality checks."
    )

class RagDocumentIntegrationTests(unittest.TestCase):
    def test_rag_context_is_empty_when_user_has_no_documents(self) -> None:
        task = build_task(title="Aegis deployment", description="Need analysis")
        with (
            patch("app.services.task_orchestrator.retrieve_relevant_chunks", return_value=[]),
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=MemoryContextResult(text=None, task_count=0, truncated=False),
            ),
        ):
            _base_context, _rag_debug, rag_context = _prepare_combined_context(task, db=MagicMock())

        self.assertEqual(rag_context.retrieved_chunks_count, 0)
        self.assertIn(rag_context.empty_reason, {"no_results", "rag_disabled"})

    def test_document_upload_creates_chunks(self) -> None:
        chunks = _chunk_text("FastAPI is async and typed. Django includes admin and ORM batteries.")
        self.assertGreater(len(chunks), 0)

    def test_rag_retrieval_returns_chunks_for_related_query(self) -> None:
        user_id = uuid.uuid4()
        with (
            patch("app.services.retrieval_service.generate_embedding", return_value=[0.1, 0.2]),
            patch(
                "app.services.retrieval_service.query_records",
                return_value=[
                    {
                        "id": "chunk-1",
                        "text": "FastAPI offers async support.",
                        "metadata": {
                            "user_id": str(user_id),
                            "document_title": "Backend guide",
                            "document_id": "doc-1",
                        },
                        "score": 0.95,
                    }
                ],
            ),
        ):
            chunks = retrieve_relevant_chunks("FastAPI", user_id=user_id, top_k=5, min_score=0.0)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].document_title, "Backend guide")

    def test_rag_retrieval_does_not_return_other_user_chunks(self) -> None:
        owner = uuid.uuid4()
        other = uuid.uuid4()
        with (
            patch("app.services.retrieval_service.generate_embedding", return_value=[0.1, 0.2]),
            patch(
                "app.services.retrieval_service.query_records",
                return_value=[
                    {
                        "id": "chunk-owner",
                        "text": "Owner context.",
                        "metadata": {"user_id": str(owner), "document_title": "Owner doc"},
                        "score": 0.91,
                    },
                    {
                        "id": "chunk-other",
                        "text": "Other context.",
                        "metadata": {"user_id": str(other), "document_title": "Other doc"},
                        "score": 0.99,
                    },
                ],
            ),
        ):
            chunks = retrieve_relevant_chunks("context", user_id=owner, top_k=5, min_score=0.0)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_id, "chunk-owner")

    def test_rag_context_respects_top_k(self) -> None:
        user_id = uuid.uuid4()
        fake_results = []
        for i in range(6):
            fake_results.append(
                {
                    "id": f"chunk-{i}",
                    "text": f"context {i}",
                    "metadata": {"user_id": str(user_id), "document_title": "Doc"},
                    "score": 0.9 - (i * 0.01),
                }
            )
        with (
            patch("app.services.retrieval_service.generate_embedding", return_value=[0.1, 0.2]),
            patch("app.services.retrieval_service.query_records", return_value=fake_results),
        ):
            chunks = retrieve_relevant_chunks("query", user_id=user_id, top_k=3, min_score=0.0)
        self.assertEqual(len(chunks), 3)

    def test_rag_context_respects_max_context_chars(self) -> None:
        chunks = [
            RetrievedChunk(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_title="Doc",
                source_name="src",
                chunk_index=0,
                text="A" * 1000,
                score=0.9,
            )
        ]
        context = build_context(chunks, max_chars=220)
        self.assertTrue(context.truncated)
        self.assertIsNotNone(context.text)

    def test_task_execution_adds_document_retrieval_trace_step(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent", title="Aegis plan")
        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title="Aegis doc",
            source_name="aegis.txt",
            chunk_index=0,
            text="Aegis architecture context with constraints and deployment notes.",
            score=0.92,
        )
        with (
            patch("app.services.task_orchestrator.retrieve_relevant_chunks", return_value=[chunk]),
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=MemoryContextResult(text=None, task_count=0, truncated=False),
            ),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda current_task, **_kwargs: _long_valid_output(current_task.title)},
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db=MagicMock())

        step_names = [step["step_name"] for step in result.execution_trace]
        self.assertIn("document_retrieval", step_names)
        retrieval_step = next(step for step in result.execution_trace if step["step_name"] == "document_retrieval")
        self.assertEqual(retrieval_step["status"], "completed")
        self.assertGreater(retrieval_step.get("rag_retrieved_chunks_count") or 0, 0)

    def test_task_execution_continues_when_rag_has_no_results(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent", title="Aegis risk review")
        with (
            patch("app.services.task_orchestrator.retrieve_relevant_chunks", return_value=[]),
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=MemoryContextResult(text=None, task_count=0, truncated=False),
            ),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda current_task, **_kwargs: _long_valid_output(current_task.title)},
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db=MagicMock())
        self.assertTrue(result.final_output)
        retrieval_step = next(step for step in result.execution_trace if step["step_name"] == "document_retrieval")
        self.assertEqual(retrieval_step["status"], "completed")
        self.assertEqual(retrieval_step.get("rag_retrieved_chunks_count"), 0)

    def test_task_execution_continues_when_rag_service_fails(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent", title="Aegis prod review")
        with (
            patch("app.services.task_orchestrator.retrieve_relevant_chunks", side_effect=RuntimeError("boom")),
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=MemoryContextResult(text=None, task_count=0, truncated=False),
            ),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda current_task, **_kwargs: _long_valid_output(current_task.title)},
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db=MagicMock())
        self.assertTrue(result.final_output)
        retrieval_step = next(step for step in result.execution_trace if step["step_name"] == "document_retrieval")
        self.assertEqual(retrieval_step["status"], "failed")
        self.assertIsNotNone(retrieval_step.get("rag_error"))

    def test_agent_prompt_includes_document_context_when_available(self) -> None:
        prompt = build_analysis_prompt(
            "Analyze deployment",
            "Need practical risks.",
            retrieved_context="Document: Aegis ADR\nContent: rollout constraints.",
        )
        self.assertIn("Available document context", prompt)
        self.assertIn("primary source for claims", prompt)

    def test_research_agent_does_not_claim_internet_access_with_rag(self) -> None:
        prompt = build_research_prompt(
            "Research backend options",
            "Use attached document.",
            retrieved_context="Document content: compare alternatives.",
        )
        self.assertIn("Never claim internet browsing", prompt)

    def test_summary_agent_can_use_document_context(self) -> None:
        prompt = build_summary_prompt(
            "Summarize architecture doc",
            "Need key points.",
            retrieved_context="Architecture doc says API-first and observability-first.",
        )
        self.assertIn("Available document context", prompt)

    def test_analysis_agent_can_use_document_context(self) -> None:
        prompt = build_analysis_prompt(
            "Analyze migration risks",
            "Need impact and mitigation",
            retrieved_context="Document mentions downtime risk and rollback.",
        )
        self.assertIn("Available document context", prompt)

    def test_planning_agent_can_use_document_context(self) -> None:
        prompt = build_planning_prompt(
            "Plan release",
            "Use provided architecture notes.",
            retrieved_context="Document suggests staged rollout and canary checks.",
        )
        self.assertIn("Available document context", prompt)

    def test_comparison_agent_can_use_document_context(self) -> None:
        prompt = build_comparison_prompt(
            "Compare FastAPI and Django",
            "Use internal notes.",
            retrieved_context="Document says API-first and admin-heavy requirements.",
        )
        self.assertIn("Available document context", prompt)

    def test_trace_does_not_store_full_large_document_text(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent", title="Aegis capacity")
        large_text = "word " * 1200
        chunk = RetrievedChunk(
            chunk_id="chunk-1",
            document_id="doc-1",
            document_title="Large doc",
            source_name="large.txt",
            chunk_index=0,
            text=large_text,
            score=0.88,
        )
        with (
            patch("app.services.task_orchestrator.retrieve_relevant_chunks", return_value=[chunk]),
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=MemoryContextResult(text=None, task_count=0, truncated=False),
            ),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda current_task, **_kwargs: _long_valid_output(current_task.title)},
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db=MagicMock())

        retrieval_step = next(step for step in result.execution_trace if step["step_name"] == "document_retrieval")
        snippets = retrieval_step.get("rag_snippets") or []
        self.assertTrue(snippets)
        self.assertLess(len(snippets[0]), 350)
        self.assertNotIn(large_text[:800], snippets[0])

    def test_rag_metadata_is_serializable_in_task_detail(self) -> None:
        task = build_task(
            status="completed",
            task_type="analysis",
            agent_name="AnalysisAgent",
            result_text="Result based on document context.",
            execution_trace=[
                {
                    "step_name": "document_retrieval",
                    "agent_name": "RAGRetriever",
                    "status": "completed",
                    "rag_enabled": True,
                    "rag_retrieved_chunks_count": 2,
                    "rag_documents_used": ["Aegis ADR"],
                    "rag_context_chars": 220,
                    "rag_snippets": ["snippet"],
                }
            ],
        )
        payload = _serialize_task(task).model_dump()
        self.assertIn("execution_trace", payload)
        self.assertEqual(payload["execution_trace"][0]["step_name"], "document_retrieval")
        self.assertEqual(payload["execution_trace"][0]["rag_retrieved_chunks_count"], 2)

    def test_rag_does_not_break_existing_comparison_analysis_planning_flows(self) -> None:
        service = SimpleNamespace(
            generate=lambda request, fallback_text=None: SimpleNamespace(
                text=(fallback_text or "Fallback text with recommendation and risk mitigation and next action."),
                provider="template",
                model="template",
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                estimated_cost=None,
                raw=None,
                fallback_used=True,
                error=None,
                retry_count=0,
                latency_ms=1,
            )
        )
        with patch("app.services.llm_service.get_llm_service", return_value=service):
            comparison = run_comparison_task(
                build_task(task_type="comparison", agent_name="ComparisonAgent", title="Compare FastAPI")
            ).lower()
            analysis = run_analysis_task(
                build_task(task_type="analysis", agent_name="AnalysisAgent", title="Analyze risks")
            ).lower()
            planning = run_planning_task(
                build_task(task_type="planning", agent_name="PlanningAgent", title="Plan release")
            ).lower()
        self.assertIn("recommend", comparison)
        self.assertIn("risk", analysis)
        self.assertIn("next action", planning)

    def test_rag_disabled_skips_retrieval(self) -> None:
        task = build_task(title="Aegis release", description="Need plan")
        with (
            patch("app.services.task_orchestrator.settings.RAG_ENABLED", False),
            patch("app.services.task_orchestrator.retrieve_relevant_chunks") as retrieve_mock,
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=MemoryContextResult(text=None, task_count=0, truncated=False),
            ),
        ):
            _base_context, _rag_debug, rag_context = _prepare_combined_context(task, db=MagicMock())
        retrieve_mock.assert_not_called()
        self.assertFalse(rag_context.enabled)

    def test_no_openrouter_call_in_rag_tests(self) -> None:
        service = LLMService(settings=SimpleNamespace(LLM_PROVIDER="template", LLM_ENABLE_REAL_CALLS=False, LLM_TIMEOUT_SECONDS=30, LLM_MAX_TOKENS=1200, LLM_TEMPERATURE=0.3, LLM_REQUEST_HARD_MAX_TOKENS=2000, OPENROUTER_MODEL="test-model", OPENAI_MODEL="gpt-5-mini", LLM_RETRY_ATTEMPTS=0, LLM_RETRY_BACKOFF_SECONDS=0.0, LLM_ENABLE_COST_ESTIMATION=False, LLM_COST_PER_1M_INPUT_TOKENS=None, LLM_COST_PER_1M_OUTPUT_TOKENS=None))
        with (
            patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider._build_client") as build_client,
            patch("app.services.llm_service.get_llm_service", return_value=service),
        ):
            run_analysis_task(build_task(task_type="analysis", agent_name="AnalysisAgent", title="Analyze deployment"))
        build_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
