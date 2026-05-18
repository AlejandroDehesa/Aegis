from abc import ABC, abstractmethod

from app.services.llm.schemas import LLMRequest, LLMResponse


class LLMProviderError(Exception):
    """Raised when a provider cannot produce a response."""


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError
