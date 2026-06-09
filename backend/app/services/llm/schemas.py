from dataclasses import dataclass, field
from typing import Literal


LLMRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class LLMMessage:
    role: LLMRole
    content: str


@dataclass(frozen=True)
class LLMRequest:
    messages: list[LLMMessage] = field(default_factory=list)
    prompt: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    metadata: dict[str, object] | None = None


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_cost: float | None = None
    raw: dict[str, object] | None = None
    fallback_used: bool = False
    error: str | None = None
    retry_count: int = 0
    latency_ms: int | None = None
