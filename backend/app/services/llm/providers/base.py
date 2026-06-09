from abc import ABC, abstractmethod

from app.services.llm.schemas import LLMRequest, LLMResponse


class LLMProviderError(Exception):
    """Raised when a provider cannot produce a response."""

    def __init__(
        self,
        message: str,
        *,
        transient: bool = False,
        configuration: bool = False,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.transient = transient
        self.configuration = configuration
        self.status_code = status_code

    @property
    def retryable(self) -> bool:
        return self.transient and not self.configuration


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError
