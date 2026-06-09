from app.services.llm.providers.base import LLMProvider, LLMProviderError
from app.services.llm.schemas import LLMRequest, LLMResponse


class MockProvider(LLMProvider):
    def generate(self, request: LLMRequest) -> LLMResponse:
        metadata = request.metadata or {}

        if bool(metadata.get("mock_raise_error")):
            raise LLMProviderError("Mock provider forced failure.")

        fallback_text = str(metadata.get("fallback_text") or "").strip()
        mock_text = str(metadata.get("mock_text") or fallback_text or "MOCK_RESPONSE_OK")
        fallback_used = bool(metadata.get("mock_fallback_used", False))

        return LLMResponse(
            text=mock_text,
            provider="mock",
            model=request.model or "mock-model",
            prompt_tokens=1,
            completion_tokens=1,
            total_tokens=2,
            fallback_used=fallback_used,
            raw={"mode": "mock"},
        )
