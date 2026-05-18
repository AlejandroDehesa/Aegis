from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

from app.services.llm.providers.base import LLMProvider, LLMProviderError
from app.services.llm.schemas import LLMMessage, LLMRequest, LLMResponse


def _extract_content(value: object) -> str:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(parts).strip()

    return ""


def _to_messages(request: LLMRequest) -> list[LLMMessage]:
    if request.messages:
        return request.messages

    if request.prompt:
        return [LLMMessage(role="user", content=request.prompt)]

    return [LLMMessage(role="user", content="No prompt provided.")]


class OpenRouterProvider(LLMProvider):
    def __init__(
        self,
        settings: object,
        *,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self._settings = settings
        self._client_factory = client_factory or self._build_default_client

    @staticmethod
    def _build_default_client(**kwargs: object) -> Any:
        try:
            from openai import OpenAI
        except ImportError as error:
            raise LLMProviderError("openai package is required for OpenRouter provider.") from error
        return OpenAI(**kwargs)

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        site_url = str(getattr(self._settings, "OPENROUTER_SITE_URL", "") or "").strip()
        app_name = str(getattr(self._settings, "OPENROUTER_APP_NAME", "") or "").strip()

        if site_url:
            headers["HTTP-Referer"] = site_url
        if app_name:
            headers["X-OpenRouter-Title"] = app_name

        return headers

    def _build_client(self) -> Any:
        return self._client_factory(
            base_url=getattr(self._settings, "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            api_key=getattr(self._settings, "OPENROUTER_API_KEY", None),
            default_headers=self._build_headers(),
            timeout=float(getattr(self._settings, "LLM_TIMEOUT_SECONDS", 30)),
        )

    @staticmethod
    def _is_transient_error(error: Exception) -> tuple[bool, int | None]:
        status_code = getattr(error, "status_code", None)
        if isinstance(status_code, int):
            if status_code == 429 or status_code >= 500:
                return True, status_code
            return False, status_code

        message = str(error).lower()
        transient_tokens = (
            "timeout",
            "timed out",
            "temporar",
            "connection",
            "rate limit",
            "429",
            "502",
            "503",
            "504",
            "server error",
            "service unavailable",
        )
        return any(token in message for token in transient_tokens), status_code

    def generate(self, request: LLMRequest) -> LLMResponse:
        enable_real_calls = bool(getattr(self._settings, "LLM_ENABLE_REAL_CALLS", False))
        metadata = request.metadata or {}
        fallback_text = str(metadata.get("fallback_text", "")).strip()

        model = request.model or getattr(self._settings, "OPENROUTER_MODEL", None)
        max_tokens = request.max_tokens or int(getattr(self._settings, "LLM_MAX_TOKENS", 1200))
        temperature = request.temperature
        if temperature is None:
            temperature = float(getattr(self._settings, "LLM_TEMPERATURE", 0.3))

        if not enable_real_calls:
            return LLMResponse(
                text=fallback_text,
                provider="openrouter",
                model=model,
                fallback_used=True,
                error="LLM real calls are disabled (LLM_ENABLE_REAL_CALLS=false).",
                raw={"mode": "disabled"},
            )

        api_key = str(getattr(self._settings, "OPENROUTER_API_KEY", "") or "").strip()
        if not api_key:
            raise LLMProviderError(
                "OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter and real calls are enabled.",
                configuration=True,
            )
        if not model:
            raise LLMProviderError(
                "OPENROUTER_MODEL is required when LLM_PROVIDER=openrouter and real calls are enabled.",
                configuration=True,
            )

        messages = [{"role": msg.role, "content": msg.content} for msg in _to_messages(request)]

        try:
            client = self._build_client()
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as error:
            transient, status_code = self._is_transient_error(error)
            raise LLMProviderError(
                f"OpenRouter request failed: {error}",
                transient=transient,
                status_code=status_code,
            ) from error

        choices = getattr(completion, "choices", []) or []
        first_choice = choices[0] if choices else None
        message = getattr(first_choice, "message", None)
        content = _extract_content(getattr(message, "content", ""))

        usage = getattr(completion, "usage", None) or SimpleNamespace(
            prompt_tokens=None,
            completion_tokens=None,
            total_tokens=None,
        )
        finish_reason = getattr(first_choice, "finish_reason", None) if first_choice else None

        return LLMResponse(
            text=content,
            provider="openrouter",
            model=getattr(completion, "model", model),
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
            estimated_cost=None,
            raw={
                "id": getattr(completion, "id", None),
                "created": getattr(completion, "created", None),
                "finish_reason": finish_reason,
            },
            fallback_used=False,
            error=None,
        )
