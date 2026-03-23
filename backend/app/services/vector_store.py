import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings

try:
    import chromadb
except ImportError:
    chromadb = None


@dataclass
class VectorStoreRecord:
    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, str]


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _cosine_similarity(first: list[float], second: list[float]) -> float:
    numerator = sum(left * right for left, right in zip(first, second, strict=False))
    first_norm = math.sqrt(sum(value * value for value in first))
    second_norm = math.sqrt(sum(value * value for value in second))

    if first_norm == 0 or second_norm == 0:
        return 0.0

    return numerator / (first_norm * second_norm)


def _load_json_store() -> list[dict[str, Any]]:
    store_path = Path(settings.LOCAL_VECTOR_STORE_PATH)

    if not store_path.exists():
        return []

    with store_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_json_store(records: list[dict[str, Any]]) -> None:
    store_path = Path(settings.LOCAL_VECTOR_STORE_PATH)
    _ensure_parent_dir(store_path)

    with store_path.open("w", encoding="utf-8") as file:
        json.dump(records, file)


def _get_chroma_collection():
    if chromadb is None:
        return None

    persist_directory = Path(settings.CHROMA_PERSIST_DIRECTORY)
    persist_directory.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_directory))
    return client.get_or_create_collection(
        name=settings.RAG_VECTOR_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def add_records(records: list[VectorStoreRecord]) -> None:
    if not records:
        return

    try:
        collection = _get_chroma_collection()
    except Exception:
        collection = None

    if collection is not None:
        collection.add(
            ids=[record.id for record in records],
            documents=[record.text for record in records],
            embeddings=[record.embedding for record in records],
            metadatas=[record.metadata for record in records],
        )
        return

    existing_records = _load_json_store()
    existing_by_id = {record["id"]: record for record in existing_records}

    for record in records:
        existing_by_id[record.id] = {
            "id": record.id,
            "text": record.text,
            "embedding": record.embedding,
            "metadata": record.metadata,
        }

    _save_json_store(list(existing_by_id.values()))


def delete_records(record_ids: list[str]) -> None:
    if not record_ids:
        return

    try:
        collection = _get_chroma_collection()
    except Exception:
        collection = None

    if collection is not None:
        collection.delete(ids=record_ids)
        return

    records = [record for record in _load_json_store() if record["id"] not in record_ids]
    _save_json_store(records)


def query_records(
    query_embedding: list[float],
    user_id: str,
    top_k: int,
) -> list[dict[str, Any]]:
    try:
        collection = _get_chroma_collection()
    except Exception:
        collection = None

    if collection is not None:
        result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"user_id": user_id},
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        return [
            {
                "id": record_id,
                "text": document,
                "metadata": metadata or {},
                "score": max(0.0, 1.0 - float(distance or 0.0)),
            }
            for record_id, document, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
                strict=False,
            )
        ]

    matches: list[dict[str, Any]] = []

    for record in _load_json_store():
        metadata = record.get("metadata", {})

        if metadata.get("user_id") != user_id:
            continue

        score = _cosine_similarity(query_embedding, record.get("embedding", []))
        matches.append(
            {
                "id": record["id"],
                "text": record["text"],
                "metadata": metadata,
                "score": score,
            }
        )

    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:top_k]
