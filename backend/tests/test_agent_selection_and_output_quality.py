from __future__ import annotations

import unittest

from app.agents.comparison_agent import run_task as run_comparison_task
from app.agents.general_assistant_agent import run_task as run_general_task
from app.agents.research_agent import run_task as run_research_task
from app.agents.summary_agent import run_task as run_summary_task
from app.services.agent_selector import select_agent
from tests.helpers import build_task


FORBIDDEN_PLACEHOLDER_PHRASES = (
    "future expansion",
    "ready for future expansion",
    "placeholder",
    "mock response",
    "todo",
    "not implemented",
    "general assistant workflow",
    "processed with the general assistant workflow",
    "dummy",
    "stub",
)


def _assert_no_placeholder_language(testcase: unittest.TestCase, output: str) -> None:
    lowered = output.lower()
    for phrase in FORBIDDEN_PLACEHOLDER_PHRASES:
        testcase.assertNotIn(phrase, lowered)


class AgentSelectionAndOutputQualityTests(unittest.TestCase):
    def test_comparison_task_selects_comparison_agent(self) -> None:
        self.assertEqual(select_agent("comparison"), "ComparisonAgent")

    def test_summary_task_selects_summary_agent(self) -> None:
        self.assertEqual(select_agent("summary"), "SummaryAgent")

    def test_research_task_selects_research_agent(self) -> None:
        self.assertEqual(select_agent("research"), "ResearchAgent")

    def test_analysis_task_selects_analysis_agent(self) -> None:
        self.assertEqual(select_agent("analysis"), "AnalysisAgent")

    def test_general_task_selects_general_agent(self) -> None:
        self.assertEqual(select_agent("general"), "GeneralAssistantAgent")

    def test_agent_selection_never_returns_none_for_valid_task_type(self) -> None:
        for task_type in ("comparison", "summary", "research", "general"):
            with self.subTest(task_type=task_type):
                self.assertIsNotNone(select_agent(task_type))

    def test_unknown_type_falls_back_safely(self) -> None:
        self.assertEqual(select_agent("unknown_type"), "GeneralAssistantAgent")

    def test_agent_output_does_not_contain_placeholder_language(self) -> None:
        task = build_task(
            title="Compara FastAPI y Django",
            description="Dame ventajas, desventajas y recomendación final.",
        )
        outputs = [
            run_general_task(task),
            run_comparison_task(task),
            run_summary_task(task),
            run_research_task(task),
        ]

        for output in outputs:
            with self.subTest(output_preview=output[:40]):
                _assert_no_placeholder_language(self, output)

    def test_general_agent_returns_useful_output(self) -> None:
        task = build_task(
            title="Ayúdame con arquitectura backend",
            description="Quiero una respuesta accionable.",
        )
        output = run_general_task(task).lower()
        self.assertNotIn("general assistant output", output)
        self.assertTrue("recommend" in output or "recomend" in output)

    def test_comparison_agent_returns_structured_comparison(self) -> None:
        task = build_task(
            title="Compare FastAPI and Django",
            description="Include advantages, disadvantages and recommendation.",
        )
        output = run_comparison_task(task).lower()
        self.assertIn("fastapi", output)
        self.assertIn("django", output)
        self.assertTrue("advantages" in output or "pros" in output)
        self.assertTrue("disadvantages" in output or "cons" in output)
        self.assertIn("recommend", output)

    def test_summary_agent_returns_actual_summary(self) -> None:
        task = build_task(
            title="Summarize this document",
            description="Keep it concise and structured.",
        )
        output = run_summary_task(task).lower()
        self.assertNotIn("this task fits a summary-oriented workflow", output)
        self.assertNotIn("prepared", output)

    def test_research_agent_returns_research_style_output(self) -> None:
        task = build_task(
            title="Research backend deployment options",
            description="Need findings and recommendation.",
        )
        output = run_research_task(task).lower()
        self.assertIn("research", output)
        self.assertNotIn("future phase", output)


if __name__ == "__main__":
    unittest.main()
