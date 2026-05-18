import re
import time

from app.core.config import settings as app_settings
from app.services.llm.providers import (
    LLMProvider,
    LLMProviderError,
    MockProvider,
    OpenRouterProvider,
    TemplateProvider,
)
from app.services.llm.schemas import LLMMessage, LLMRequest, LLMResponse


ALLOWED_PROVIDERS = {"template", "mock", "openrouter"}
SECRET_TOKEN_PATTERN = re.compile(r"(sk-[A-Za-z0-9_\-]+)")
BEARER_TOKEN_PATTERN = re.compile(r"(bearer\s+)([A-Za-z0-9_\-\.]+)", re.IGNORECASE)


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
        normalized_name = provider_name.strip().lower()
        if normalized_name not in ALLOWED_PROVIDERS:
            raise LLMProviderError(
                f"Invalid LLM_PROVIDER '{normalized_name}'. Allowed values: {sorted(ALLOWED_PROVIDERS)}.",
                configuration=True,
            )
        return normalized_name

    def _get_provider(self) -> LLMProvider:
        provider_name = self._provider_name()
        if provider_name in self._provider_overrides:
            return self._provider_overrides[provider_name]

        if provider_name == "mock":
            return MockProvider()
        if provider_name == "openrouter":
            return OpenRouterProvider(self._settings)
        if provider_name == "template":
            return TemplateProvider()
        raise LLMProviderError(
            f"Invalid LLM provider '{provider_name}'.",
            configuration=True,
        )

    @staticmethod
    def _sanitize_error_message(message: str, api_key: str | None = None) -> str:
        sanitized = (message or "").strip()
        sanitized = SECRET_TOKEN_PATTERN.sub("sk-or-***", sanitized)
        sanitized = BEARER_TOKEN_PATTERN.sub(r"\1***", sanitized)
        if api_key:
            sanitized = sanitized.replace(api_key, "sk-or-***")
        return sanitized

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
        if temperature < 0.0 or temperature > 2.0:
            raise LLMProviderError(
                "LLM_TEMPERATURE must be between 0.0 and 2.0.",
                configuration=True,
            )

        max_tokens = request.max_tokens
        if max_tokens is None:
            max_tokens = int(getattr(self._settings, "LLM_MAX_TOKENS", 1200))
        if max_tokens <= 0:
            raise LLMProviderError(
                "LLM max_tokens must be greater than zero.",
                configuration=True,
            )
        hard_max_tokens = int(getattr(self._settings, "LLM_REQUEST_HARD_MAX_TOKENS", 2000))
        if hard_max_tokens <= 0:
            raise LLMProviderError(
                "LLM_REQUEST_HARD_MAX_TOKENS must be greater than zero.",
                configuration=True,
            )
        max_tokens = min(max_tokens, hard_max_tokens)

        timeout_seconds = float(getattr(self._settings, "LLM_TIMEOUT_SECONDS", 30))
        if timeout_seconds <= 0:
            raise LLMProviderError(
                "LLM_TIMEOUT_SECONDS must be greater than zero.",
                configuration=True,
            )

        return LLMRequest(
            messages=messages,
            prompt=request.prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            metadata=metadata,
        )

    def _validate_provider_runtime_requirements(self, provider_name: str, request: LLMRequest) -> None:
        if provider_name != "openrouter":
            return

        if not bool(getattr(self._settings, "LLM_ENABLE_REAL_CALLS", False)):
            return

        model = str(request.model or "").strip()
        if not model:
            raise LLMProviderError(
                "OPENROUTER_MODEL is required when LLM_PROVIDER=openrouter and real calls are enabled.",
                configuration=True,
            )

        api_key = str(getattr(self._settings, "OPENROUTER_API_KEY", "") or "").strip()
        if not api_key:
            raise LLMProviderError(
                "OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter and real calls are enabled.",
                configuration=True,
            )

    def _retry_attempts(self) -> int:
        return max(0, int(getattr(self._settings, "LLM_RETRY_ATTEMPTS", 1)))

    def _retry_backoff_seconds(self) -> float:
        backoff = float(getattr(self._settings, "LLM_RETRY_BACKOFF_SECONDS", 0.5))
        return max(backoff, 0.0)

    def _should_retry(self, provider_name: str, error: LLMProviderError, retry_index: int) -> bool:
        if provider_name != "openrouter":
            return False
        if not error.retryable:
            return False
        return retry_index < self._retry_attempts()

    @staticmethod
    def _estimate_cost_from_tokens(
        *,
        prompt_tokens: int | None,
        completion_tokens: int | None,
        input_price_per_1m: float | None,
        output_price_per_1m: float | None,
    ) -> float | None:
        if prompt_tokens is None or completion_tokens is None:
            return None
        if input_price_per_1m is None or output_price_per_1m is None:
            return None

        prompt_cost = (prompt_tokens / 1_000_000.0) * input_price_per_1m
        completion_cost = (completion_tokens / 1_000_000.0) * output_price_per_1m
        return prompt_cost + completion_cost

    def _apply_cost_estimation(self, response: LLMResponse) -> LLMResponse:
        if response.estimated_cost is not None:
            return response
        if not bool(getattr(self._settings, "LLM_ENABLE_COST_ESTIMATION", True)):
            return response

        estimated_cost = self._estimate_cost_from_tokens(
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            input_price_per_1m=getattr(self._settings, "LLM_COST_PER_1M_INPUT_TOKENS", None),
            output_price_per_1m=getattr(self._settings, "LLM_COST_PER_1M_OUTPUT_TOKENS", None),
        )
        if estimated_cost is None:
            return response

        return LLMResponse(
            text=response.text,
            provider=response.provider,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            estimated_cost=estimated_cost,
            raw=response.raw,
            fallback_used=response.fallback_used,
            error=response.error,
            retry_count=response.retry_count,
            latency_ms=response.latency_ms,
        )

    def _fallback_response(
        self,
        *,
        provider_name: str,
        request: LLMRequest,
        error: LLMProviderError,
        retry_count: int,
        latency_ms: int | None,
    ) -> LLMResponse:
        fallback_response = TemplateProvider().generate(request)
        sanitized_error = self._sanitize_error_message(
            str(error),
            api_key=str(getattr(self._settings, "OPENROUTER_API_KEY", "") or "").strip() or None,
        )
        return LLMResponse(
            text=fallback_response.text,
            provider=provider_name,
            model=request.model,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            estimated_cost=None,
            raw={
                "upstream_provider": provider_name,
                "effective_provider": "template",
            },
            fallback_used=True,
            error=sanitized_error,
            retry_count=retry_count,
            latency_ms=latency_ms,
        )

    def generate(
        self,
        request: LLMRequest,
        fallback_text: str | None = None,
    ) -> LLMResponse:
        normalized_request = self._build_request(request, fallback_text)
        provider_name = self._provider_name()
        self._validate_provider_runtime_requirements(provider_name, normalized_request)
        provider = self._get_provider()
        retry_count = 0
        last_error: LLMProviderError | None = None
        last_latency_ms: int | None = None

        for attempt in range(self._retry_attempts() + 1):
            started = time.perf_counter()
            try:
                response = provider.generate(normalized_request)
                last_latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
                if not response.text.strip():
                    raise LLMProviderError(
                        "Provider returned an empty response.",
                        transient=False,
                        configuration=False,
                    )
                normalized_response = LLMResponse(
                    text=response.text,
                    provider=response.provider,
                    model=response.model,
                    prompt_tokens=response.prompt_tokens,
                    completion_tokens=response.completion_tokens,
                    total_tokens=response.total_tokens,
                    estimated_cost=response.estimated_cost,
                    raw=response.raw,
                    fallback_used=response.fallback_used,
                    error=response.error,
                    retry_count=attempt,
                    latency_ms=response.latency_ms if response.latency_ms is not None else last_latency_ms,
                )
                return self._apply_cost_estimation(normalized_response)
            except LLMProviderError as error:
                retry_count = attempt
                last_error = error
                last_latency_ms = max(int((time.perf_counter() - started) * 1000), 0)
                if self._should_retry(provider_name, error, attempt):
                    backoff = self._retry_backoff_seconds() * (attempt + 1)
                    if backoff > 0:
                        time.sleep(backoff)
                    continue
                break

        if last_error is not None:
            return self._fallback_response(
                provider_name=provider_name,
                request=normalized_request,
                error=last_error,
                retry_count=retry_count,
                latency_ms=last_latency_ms,
            )

        fallback_response = TemplateProvider().generate(normalized_request)
        return LLMResponse(
            text=fallback_response.text,
            provider=provider_name,
            model=normalized_request.model,
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
            estimated_cost=None,
            raw={"upstream_provider": provider_name, "effective_provider": "template"},
            fallback_used=True,
            error="Unknown provider failure.",
            retry_count=retry_count,
            latency_ms=last_latency_ms,
        )

    def generate_legacy_compatible_text(
        self,
        request: LLMRequest,
        fallback_text: str | None = None,
    ) -> LLMResponse:
        try:
            return self.generate(request=request, fallback_text=fallback_text)
        except LLMProviderError as error:
            fallback_response = TemplateProvider().generate(
                self._build_request(request=request, fallback_text=fallback_text)
            )
            return LLMResponse(
                text=fallback_response.text,
                provider=self._provider_name(),
                model=request.model or getattr(self._settings, "OPENROUTER_MODEL", None),
                prompt_tokens=None,
                completion_tokens=None,
                total_tokens=None,
                estimated_cost=None,
                raw={"upstream_provider": self._provider_name(), "effective_provider": "template"},
                fallback_used=True,
                error=self._sanitize_error_message(str(error)),
                retry_count=0,
                latency_ms=None,
            )
