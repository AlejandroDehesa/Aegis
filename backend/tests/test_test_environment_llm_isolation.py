from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app.agents.comparison_agent import run_task as run_comparison_task
from app.core.config import settings
from app.services.llm.service import LLMService
from app.services.llm.schemas import LLMRequest
from tests.helpers import build_task


class TestEnvironmentLLMIsolationTests(unittest.TestCase):
    def test_test_suite_forces_llm_provider_to_template_or_mock(self) -> None:
        self.assertIn(settings.LLM_PROVIDER, {"template", "mock"})
        self.assertFalse(settings.LLM_ENABLE_REAL_CALLS)

    def test_openrouter_is_not_used_in_automatic_tests_even_if_local_env_has_openrouter(self) -> None:
        # Even if the local runtime .env config uses OpenRouter, test bootstrap must override it.
        self.assertNotEqual(os.getenv("LLM_PROVIDER"), "openrouter")
        self.assertEqual(os.getenv("LLM_ENABLE_REAL_CALLS"), "false")

        task = build_task(
            task_type="comparison",
            agent_name="ComparisonAgent",
            title="Compare FastAPI and Django",
            description="Need recommendation with pros and cons.",
        )

        with patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider._build_client") as build_client:
            output = run_comparison_task(task).lower()

        build_client.assert_not_called()
        self.assertIn("recommend", output)

    def test_no_real_openrouter_api_key_is_required_for_backend_tests(self) -> None:
        # Template mode should work even when OPENROUTER_API_KEY is blank.
        self.assertEqual(os.getenv("OPENROUTER_API_KEY"), "")
        service = LLMService()
        response = service.generate(LLMRequest(prompt="hello"), fallback_text="fallback")
        self.assertEqual(response.provider, "template")
        self.assertEqual(response.text, "fallback")


if __name__ == "__main__":
    unittest.main()
