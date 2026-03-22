from functools import lru_cache

from app.core.config import settings


@lru_cache
def get_openai_client():
    if not settings.OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    return OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_text(prompt: str, fallback_text: str = "") -> str:
    client = get_openai_client()

    if client is None:
        return fallback_text

    try:
        response = client.responses.create(
            model=settings.OPENAI_MODEL,
            input=prompt,
        )
        output_text = (response.output_text or "").strip()

        if output_text:
            return output_text
    except Exception:
        pass

    return fallback_text
