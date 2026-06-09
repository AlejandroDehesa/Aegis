from functools import lru_cache

from app.core.config import settings
from app.services.llm.schemas import LLMRequest
from app.services.llm.service import LLMService


@lru_cache
def get_openai_client():
    if not settings.OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    return OpenAI(api_key=settings.OPENAI_API_KEY)


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()


def generate(
    request: LLMRequest,
    fallback_text: str | None = None,
):
    return get_llm_service().generate(request=request, fallback_text=fallback_text)


def generate_text(prompt: str, fallback_text: str = "") -> str:
    try:
        response = get_llm_service().generate(
            request=LLMRequest(prompt=prompt),
            fallback_text=fallback_text,
        )
        if response.text.strip():
            return response.text.strip()
    except Exception:
        pass

    return fallback_text
