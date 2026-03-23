import hashlib
import math

from app.core.config import settings
from app.services.llm_service import get_openai_client


FALLBACK_EMBEDDING_DIMENSION = 64


def _normalize_vector(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))

    if magnitude == 0:
        return vector

    return [value / magnitude for value in vector]


def _generate_fallback_embedding(text: str) -> list[float]:
    vector = [0.0] * FALLBACK_EMBEDDING_DIMENSION
    tokens = [token for token in text.lower().split() if token]

    if not tokens:
        tokens = list(text.lower()) or ["empty"]

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % FALLBACK_EMBEDDING_DIMENSION
        vector[bucket] += 1.0

    return _normalize_vector(vector)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    client = get_openai_client()

    if client is None:
        return [_generate_fallback_embedding(text) for text in texts]

    try:
        response = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=texts,
        )
        return [list(item.embedding) for item in response.data]
    except Exception:
        return [_generate_fallback_embedding(text) for text in texts]


def generate_embedding(text: str) -> list[float]:
    embeddings = generate_embeddings([text])
    return embeddings[0] if embeddings else _generate_fallback_embedding(text)
