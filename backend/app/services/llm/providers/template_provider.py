from app.services.llm.providers.base import LLMProvider
from app.services.llm.schemas import LLMRequest, LLMResponse


DEFAULT_TEMPLATE_TEXT = (
    "Aegis generated a safe fallback response. "
    "Provide a fallback_text for task-specific output."
)


class TemplateProvider(LLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        metadata = request.metadata or {}
        fallback_text = str(metadata.get("fallback_text", "")).strip()

        return LLMResponse(
            text=fallback_text or DEFAULT_TEMPLATE_TEXT,
            provider="template",
            model=request.model,
            fallback_used=True,
            raw={"mode": "template_fallback"},
        )
