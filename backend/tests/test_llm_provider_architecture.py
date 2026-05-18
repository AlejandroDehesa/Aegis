from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.services.llm.providers.base import LLMProvider, LLMProviderError
from app.services.llm.providers.mock_provider import MockProvider
from app.services.llm.providers.openrouter_provider import OpenRouterProvider
from app.services.llm.providers.template_provider import TemplateProvider
from app.services.llm.schemas import LLMMessage, LLMRequest, LLMResponse
from app.services.llm.service import LLMService
from app.services.llm_service import generate_text


def _build_settings(**overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = {
        "LLM_PROVIDER": "template",
        "LLM_ENABLE_REAL_CALLS": False,
        "LLM_TIMEOUT_SECONDS": 30,
        "LLM_MAX_TOKENS": 1200,
        "LLM_TEMPERATURE": 0.3,
        "LLM_RETRY_ATTEMPTS": 1,
        "LLM_RETRY_BACKOFF_SECONDS": 0.0,
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
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class _FailingProvider(LLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        raise LLMProviderError("forced provider error")


class LLMProviderArchitectureTests(unittest.TestCase):
    def test_template_provider_returns_fallback_text(self) -> None:
        provider = TemplateProvider()
        request = LLMRequest(prompt="hola", metadata={"fallback_text": "fallback demo"})
        response = provider.generate(request)
        self.assertEqual(response.text, "fallback demo")
        self.assertEqual(response.provider, "template")
        self.assertTrue(response.fallback_used)

    def test_template_provider_returns_safe_text_without_fallback(self) -> None:
        provider = TemplateProvider()
        response = provider.generate(LLMRequest(prompt="hola"))
        self.assertIn("safe fallback response", response.text.lower())
        self.assertEqual(response.provider, "template")
        self.assertTrue(response.fallback_used)

    def test_mock_provider_returns_deterministic_response(self) -> None:
        provider = MockProvider()
        request = LLMRequest(prompt="hola", metadata={"mock_text": "DETERMINISTIC_OUTPUT"})
        response = provider.generate(request)
        self.assertEqual(response.text, "DETERMINISTIC_OUTPUT")
        self.assertEqual(response.provider, "mock")
        self.assertEqual(response.model, "mock-model")

    def test_llm_service_uses_template_by_default(self) -> None:
        service = LLMService(settings=_build_settings())
        response = service.generate(LLMRequest(prompt="hola"), fallback_text="fallback default")
        self.assertEqual(response.provider, "template")
        self.assertEqual(response.text, "fallback default")
        self.assertTrue(response.fallback_used)

    def test_llm_service_uses_mock_provider_in_test_mode(self) -> None:
        service = LLMService(settings=_build_settings(LLM_PROVIDER="mock"))
        response = service.generate(LLMRequest(prompt="hola"))
        self.assertEqual(response.provider, "mock")
        self.assertEqual(response.text, "MOCK_RESPONSE_OK")
        self.assertFalse(response.fallback_used)

    def test_generate_text_legacy_wrapper_preserves_fallback_behavior(self) -> None:
        fake_service = SimpleNamespace(
            generate=lambda request, fallback_text=None: (_ for _ in ()).throw(RuntimeError("boom"))
        )

        with patch("app.services.llm_service.get_llm_service", return_value=fake_service):
            result = generate_text("prompt", fallback_text="legacy fallback")

        self.assertEqual(result, "legacy fallback")

    def test_openrouter_provider_requires_api_key_when_real_calls_enabled(self) -> None:
        settings = _build_settings(LLM_ENABLE_REAL_CALLS=True, OPENROUTER_API_KEY=None)
        provider = OpenRouterProvider(settings)

        with self.assertRaises(LLMProviderError):
            provider.generate(LLMRequest(prompt="hola"))

    def test_openrouter_provider_does_not_call_external_api_when_real_calls_disabled(self) -> None:
        called = {"value": False}

        def _unexpected_client_factory(**kwargs: object) -> object:
            called["value"] = True
            raise AssertionError("Should not build client when real calls are disabled.")

        settings = _build_settings(LLM_ENABLE_REAL_CALLS=False, OPENROUTER_API_KEY="dummy-key")
        provider = OpenRouterProvider(settings, client_factory=_unexpected_client_factory)
        response = provider.generate(
            LLMRequest(prompt="hola", metadata={"fallback_text": "disabled fallback"})
        )

        self.assertFalse(called["value"])
        self.assertEqual(response.text, "disabled fallback")
        self.assertEqual(response.provider, "openrouter")
        self.assertTrue(response.fallback_used)

    def test_openrouter_provider_builds_expected_messages_payload(self) -> None:
        captured: dict[str, object] = {}

        class _FakeCompletions:
            def create(self, **kwargs: object) -> object:
                captured.update(kwargs)
                return SimpleNamespace(
                    id="cmp_1",
                    created=123,
                    model="openrouter/test-model",
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content="Remote answer"),
                            finish_reason="stop",
                        )
                    ],
                    usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7, total_tokens=18),
                )

        class _FakeClient:
            def __init__(self) -> None:
                self.chat = SimpleNamespace(completions=_FakeCompletions())

        def _client_factory(**kwargs: object) -> object:
            captured["client_kwargs"] = kwargs
            return _FakeClient()

        settings = _build_settings(LLM_ENABLE_REAL_CALLS=True, OPENROUTER_API_KEY="dummy-key")
        provider = OpenRouterProvider(settings, client_factory=_client_factory)
        response = provider.generate(
            LLMRequest(
                messages=[LLMMessage(role="system", content="rules"), LLMMessage(role="user", content="hola")],
                model="openrouter/custom-model",
                temperature=0.1,
                max_tokens=77,
            )
        )

        self.assertEqual(captured["model"], "openrouter/custom-model")
        self.assertEqual(captured["temperature"], 0.1)
        self.assertEqual(captured["max_tokens"], 77)
        self.assertEqual(
            captured["messages"],
            [
                {"role": "system", "content": "rules"},
                {"role": "user", "content": "hola"},
            ],
        )
        self.assertEqual(response.text, "Remote answer")
        self.assertEqual(response.provider, "openrouter")
        self.assertFalse(response.fallback_used)

    def test_llm_response_contains_provider_model_tokens_fields(self) -> None:
        class _FakeCompletions:
            def create(self, **kwargs: object) -> object:
                return SimpleNamespace(
                    id="cmp_2",
                    created=456,
                    model="openrouter/test-model",
                    choices=[SimpleNamespace(message=SimpleNamespace(content="done"), finish_reason="stop")],
                    usage=SimpleNamespace(prompt_tokens=3, completion_tokens=4, total_tokens=7),
                )

        class _FakeClient:
            def __init__(self) -> None:
                self.chat = SimpleNamespace(completions=_FakeCompletions())

        provider = OpenRouterProvider(
            _build_settings(LLM_ENABLE_REAL_CALLS=True, OPENROUTER_API_KEY="dummy-key"),
            client_factory=lambda **kwargs: _FakeClient(),
        )
        response = provider.generate(LLMRequest(prompt="hola"))

        self.assertEqual(response.provider, "openrouter")
        self.assertEqual(response.model, "openrouter/test-model")
        self.assertEqual(response.prompt_tokens, 3)
        self.assertEqual(response.completion_tokens, 4)
        self.assertEqual(response.total_tokens, 7)

    def test_llm_service_falls_back_when_openrouter_raises(self) -> None:
        service = LLMService(
            settings=_build_settings(LLM_PROVIDER="openrouter"),
            provider_overrides={"openrouter": _FailingProvider()},
        )
        response = service.generate(LLMRequest(prompt="hola"), fallback_text="service fallback")

        self.assertEqual(response.provider, "openrouter")
        self.assertEqual(response.text, "service fallback")
        self.assertTrue(response.fallback_used)
        self.assertIn("forced provider error", response.error or "")
        self.assertEqual((response.raw or {}).get("effective_provider"), "template")

    def test_no_real_openrouter_call_in_unit_tests(self) -> None:
        settings = _build_settings(LLM_PROVIDER="template")
        service = LLMService(settings=settings)

        with patch("app.services.llm.providers.openrouter_provider.OpenRouterProvider.generate") as openrouter_generate:
            service.generate(LLMRequest(prompt="hola"), fallback_text="ok")

        openrouter_generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
