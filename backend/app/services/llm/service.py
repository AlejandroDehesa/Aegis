from app.core.config import settings as app_settings
from app.services.llm.providers import (
    LLMProvider,
    LLMProviderError,
    MockProvider,
    OpenRouterProvider,
    TemplateProvider,
)
from app.services.llm.schemas import LLMMessage, LLMRequest, LLMResponse


class LLMService:
    def __init__(
        self,
        settings: object | None = None,
        *,
        provider_overrides: dict[str, LLMProvider] | None = None,
    ) -> None:
        self._settings = settings or app_settings
        self._provider_overrides = provider_overrides or {}

    def _provider_name(self) -> str:
        provider_name = str(getattr(self._settings, "LLM_PROVIDER", "template") or "template")
        return provider_name.strip().lower()

    def _get_provider(self) -> LLMProvider:
        provider_name = self._provider_name()
        if provider_name in self._provider_overrides:
            return self._provider_overrides[provider_name]

        if provider_name == "mock":
            return MockProvider()
        if provider_name == "openrouter":
            return OpenRouterProvider(self._settings)
        return TemplateProvider()

    def _build_request(
        self,
        request: LLMRequest,
        fallback_text: str | None,
    ) -> LLMRequest:
        metadata = dict(request.metadata or {})
        if fallback_text is not None:
            metadata["fallback_text"] = fallback_text

        messages = request.messages
        if not messages and request.prompt:
            messages = [LLMMessage(role="user", content=request.prompt)]

        model = request.model or getattr(self._settings, "OPENROUTER_MODEL", None) or getattr(
            self._settings,
            "OPENAI_MODEL",
            None,
        )
        temperature = request.temperature
        if temperature is None:
            temperature = float(getattr(self._settings, "LLM_TEMPERATURE", 0.3))
        max_tokens = request.max_tokens
        if max_tokens is None:
            max_tokens = int(getattr(self._settings, "LLM_MAX_TOKENS", 1200))

        return LLMRequest(
            messages=messages,
            prompt=request.prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )

    def generate(
        self,
        request: LLMRequest,
        fallback_text: str | None = None,
    ) -> LLMResponse:
        normalized_request = self._build_request(request, fallback_text)
        provider = self._get_provider()

        try:
            response = provider.generate(normalized_request)
        except LLMProviderError as error:
            fallback_response = TemplateProvider().generate(normalized_request)
            return LLMResponse(
                text=fallback_response.text,
                provider=fallback_response.provider,
                model=normalized_request.model,
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                estimated_cost=None,
                raw={"upstream_provider": self._provider_name()},
                fallback_used=True,
                error=str(error),
            )

        if response.text.strip():
            return response

        fallback_response = TemplateProvider().generate(normalized_request)
        return LLMResponse(
            text=fallback_response.text,
            provider=fallback_response.provider,
            model=response.model or normalized_request.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            estimated_cost=response.estimated_cost,
            raw=response.raw,
            fallback_used=True,
            error=response.error,
        )
