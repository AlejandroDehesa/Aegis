from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.api.v1.tasks import _normalize_trace_step
from app.schemas.task import TaskExecutionStepRead
from app.services.task_orchestrator import (
    OrchestrationRagDebugInfo,
    orchestrate_task,
)
from tests.helpers import build_task


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


class ExecutionTraceContractTests(unittest.TestCase):
    @staticmethod
    def _valid_comparison_output() -> str:
        return (
            "For this test task comparison, FastAPI provides faster API iteration while Django "
            "offers a richer built-in admin stack. Advantages and disadvantages were reviewed, "
            "and the recommendation is to use FastAPI for API-first delivery."
        )

    def test_execution_trace_includes_classification_step(self) -> None:
        task = build_task(task_type="comparison")
        db = MagicMock()

        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {
                    "ResearchAgent": lambda *_args, **_kwargs: self._valid_comparison_output(),
                    "ComparisonAgent": lambda *_args, **_kwargs: self._valid_comparison_output(),
                },
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db)

        step_names = {step["step_name"] for step in result.execution_trace}
        self.assertIn("classification", step_names)

    def test_execution_trace_includes_agent_selection_step(self) -> None:
        task = build_task(task_type="comparison")
        db = MagicMock()

        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {
                    "ResearchAgent": lambda *_args, **_kwargs: self._valid_comparison_output(),
                    "ComparisonAgent": lambda *_args, **_kwargs: self._valid_comparison_output(),
                },
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db)

        step_names = {step["step_name"] for step in result.execution_trace}
        self.assertIn("agent_selection", step_names)

    def test_execution_trace_steps_match_schema(self) -> None:
        task = build_task(task_type="comparison")
        db = MagicMock()

        with (
            patch("app.services.task_orchestrator._prepare_combined_context", return_value=(None, _empty_rag_debug())),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {
                    "ResearchAgent": lambda *_args, **_kwargs: self._valid_comparison_output(),
                    "ComparisonAgent": lambda *_args, **_kwargs: self._valid_comparison_output(),
                },
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db)

        for step in result.execution_trace:
            TaskExecutionStepRead.model_validate(step)

    def test_seed_demo_trace_matches_current_schema(self) -> None:
        legacy_seed_step = {
            "step": "classification",
            "status": "completed",
            "summary": "Task classified as comparison.",
        }

        normalized = _normalize_trace_step(legacy_seed_step, "ComparisonAgent")
        TaskExecutionStepRead.model_validate(normalized)


if __name__ == "__main__":
    unittest.main()
