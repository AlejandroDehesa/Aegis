from dataclasses import dataclass

from app.services.llm.schemas import LLMResponse


@dataclass(frozen=True)
class AgentExecutionResult:
    text: str
    llm_provider: str | None = None
    llm_model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None
    fallback_used: bool = False
    llm_error: str | None = None
    llm_retry_count: int = 0
    llm_latency_ms: int | None = None

    @classmethod
    def from_llm_response(cls, response: LLMResponse) -> "AgentExecutionResult":
        return cls(
            text=response.text,
            llm_provider=response.provider,
            llm_model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            estimated_cost=response.estimated_cost,
            fallback_used=response.fallback_used,
            llm_error=response.error,
            llm_retry_count=response.retry_count,
            llm_latency_ms=response.latency_ms,
        )
