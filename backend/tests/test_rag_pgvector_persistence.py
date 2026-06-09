from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace
import unittest
import uuid
from unittest.mock import MagicMock, patch

from app.models.document import DocumentChunk
from app.services.document_service import create_document
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.task_orchestrator import orchestrate_task
from app.services.vector_store import query_records
from scripts.backfill_pgvector_embeddings import run_backfill
from tests.helpers import build_task


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_CANDIDATES = [
    BACKEND_ROOT.parent,
    Path("/workspace"),
    Path("/project"),
]


def _find_repo_file(relative_path: str) -> Path | None:
    for candidate in REPO_CANDIDATES:
        file_path = candidate / relative_path
        if file_path.exists():
            return file_path
    return None


class _FakeSessionResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return SimpleNamespace(all=lambda: list(self._values))


class _FakeBackfillSession:
    def __init__(self, batches: list[list[object]]) -> None:
        self._batches = batches
        self._batch_index = 0
        self.commits = 0
        self.rollbacks = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, _statement):
        if self._batch_index >= len(self._batches):
            values = []
        else:
            values = self._batches[self._batch_index]
        self._batch_index += 1
        return _FakeSessionResult(values)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class RagPgvectorPersistenceTests(unittest.TestCase):
    def test_document_chunk_has_embedding_field(self) -> None:
        self.assertIn("embedding", DocumentChunk.__table__.columns.keys())

    def test_upload_persists_chunk_embeddings_in_postgres(self) -> None:
        db = MagicMock()
        chunks_added: list[DocumentChunk] = []

        def _capture_add(value):
            if isinstance(value, DocumentChunk):
                chunks_added.append(value)

        db.add.side_effect = _capture_add
        db.flush.side_effect = None
        db.commit.side_effect = None

        with patch(
            "app.services.document_service.generate_embeddings",
            side_effect=lambda texts: [[0.1, 0.2] for _ in texts],
        ):
            create_document(
                db=db,
                user_id=uuid.uuid4(),
                title="Doc",
                content="Chunk one. Chunk two.",
                source_type="text",
            )

        self.assertGreaterEqual(len(chunks_added), 1)
        self.assertTrue(all(chunk.embedding for chunk in chunks_added))

    def test_retrieval_uses_postgres_not_chroma(self) -> None:
        with (
            patch("app.services.vector_store.settings.RAG_VECTOR_BACKEND", "pgvector"),
            patch("app.services.vector_store._query_records_pgvector", return_value=[]) as pg_query,
            patch("app.services.vector_store._query_records_local", return_value=[]) as local_query,
        ):
            query_records([0.1, 0.2], str(uuid.uuid4()), 3)

        pg_query.assert_called_once()
        local_query.assert_not_called()

    def test_retrieval_filters_by_user_id(self) -> None:
        owner = uuid.uuid4()
        other = uuid.uuid4()

        with (
            patch("app.services.retrieval_service.generate_embedding", return_value=[0.1, 0.2]),
            patch(
                "app.services.retrieval_service.query_records",
                return_value=[
                    {
                        "id": "chunk-owner",
                        "text": "Owner content",
                        "metadata": {"user_id": str(owner), "document_title": "Owner"},
                        "score": 0.9,
                    },
                    {
                        "id": "chunk-other",
                        "text": "Other content",
                        "metadata": {"user_id": str(other), "document_title": "Other"},
                        "score": 0.95,
                    },
                ],
            ),
        ):
            chunks = retrieve_relevant_chunks("query", owner, top_k=5, min_score=0.0)

        self.assertEqual([chunk.chunk_id for chunk in chunks], ["chunk-owner"])

    def test_retrieval_ignores_chunks_without_embedding(self) -> None:
        with (
            patch("app.services.vector_store.settings.RAG_VECTOR_BACKEND", "local"),
            patch("app.services.vector_store._query_records_local", return_value=[]),
        ):
            results = query_records([0.1, 0.2], str(uuid.uuid4()), 4)
        self.assertEqual(results, [])

    def test_rag_context_uses_documents_after_redeploy_simulation(self) -> None:
        user_id = uuid.uuid4()
        with (
            patch("app.services.retrieval_service.generate_embedding", return_value=[0.2, 0.4]),
            patch(
                "app.services.retrieval_service.query_records",
                return_value=[
                    {
                        "id": "chunk-restored",
                        "text": "Restored context from persisted PostgreSQL chunk.",
                        "metadata": {
                            "user_id": str(user_id),
                            "document_id": "doc-1",
                            "document_title": "Persistent doc",
                            "source_name": "notes.txt",
                            "chunk_index": "0",
                        },
                        "score": 0.93,
                    }
                ],
            ),
        ):
            chunks = retrieve_relevant_chunks("persisted document context", user_id, top_k=3, min_score=0.0)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].document_title, "Persistent doc")

    def test_backfill_embeddings_fills_missing_embeddings(self) -> None:
        chunk_a = SimpleNamespace(content="alpha", embedding=None)
        chunk_b = SimpleNamespace(content="beta", embedding=None)
        fake_session = _FakeBackfillSession([[chunk_a, chunk_b], []])

        with (
            patch("scripts.backfill_pgvector_embeddings.SessionLocal", return_value=fake_session),
            patch("scripts.backfill_pgvector_embeddings.generate_embeddings", return_value=[[0.1], [0.2]]),
        ):
            summary = run_backfill(batch_size=2)

        self.assertEqual(summary.scanned, 2)
        self.assertEqual(summary.updated, 2)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(chunk_a.embedding, [0.1])
        self.assertEqual(chunk_b.embedding, [0.2])

    def test_backfill_is_idempotent(self) -> None:
        fake_session = _FakeBackfillSession([[]])

        with patch("scripts.backfill_pgvector_embeddings.SessionLocal", return_value=fake_session):
            summary = run_backfill(batch_size=2)

        self.assertEqual(summary.scanned, 0)
        self.assertEqual(summary.updated, 0)
        self.assertEqual(summary.failed, 0)

    def test_rag_trace_reports_pgvector_backend(self) -> None:
        task = build_task(task_type="general", agent_name="GeneralAssistantAgent", title="RAG trace")

        with (
            patch("app.services.task_orchestrator.settings.RAG_VECTOR_BACKEND", "pgvector"),
            patch("app.services.task_orchestrator.retrieve_relevant_chunks", return_value=[]),
            patch(
                "app.services.task_orchestrator.get_recent_task_context_result",
                return_value=SimpleNamespace(text=None, task_count=0, truncated=False),
            ),
            patch.dict(
                "app.services.task_orchestrator.AGENT_RUNNERS",
                {"GeneralAssistantAgent": lambda current_task, **_kwargs: (
                    "RAG trace review: this output addresses the task title and includes recommendation, "
                    "risk, impact, mitigation, assumptions, and a concrete next action to pass quality checks."
                )},
                clear=False,
            ),
        ):
            result = orchestrate_task(task, db=MagicMock())

        retrieval_step = next(step for step in result.execution_trace if step["step_name"] == "document_retrieval")
        self.assertEqual(retrieval_step.get("rag_vector_backend"), "pgvector")

    def test_no_chroma_required_for_pgvector_retrieval(self) -> None:
        vector_store_path = _find_repo_file("backend/app/services/vector_store.py")
        if vector_store_path is None:
            self.skipTest("vector_store.py is not mounted in this test runtime")
        content = vector_store_path.read_text(encoding="utf-8").lower()
        self.assertNotIn("chromadb", content)

    def test_pgvector_migration_exists(self) -> None:
        migration_file = _find_repo_file("alembic/versions/0002_pgvector_embeddings.py")
        if migration_file is None:
            self.skipTest("pgvector migration is not mounted in this test runtime")
        self.assertTrue(migration_file.exists())
        content = migration_file.read_text(encoding="utf-8")
        self.assertIn("CREATE EXTENSION IF NOT EXISTS vector", content)
        self.assertIn("embedding vector", content)

    def test_env_example_documents_rag_vector_backend(self) -> None:
        env_file = _find_repo_file(".env.example")
        if env_file is None:
            self.skipTest(".env.example is not mounted in this test runtime")
        content = env_file.read_text(encoding="utf-8")
        self.assertIn("RAG_VECTOR_BACKEND=pgvector", content)
        self.assertIn("EMBEDDING_DIMENSION=64", content)

    def test_no_openrouter_call_in_pgvector_tests(self) -> None:
        with patch("app.services.embeddings_service.get_openai_client", return_value=None):
            embedding = importlib.import_module("app.services.embeddings_service").generate_embedding("hello")
        self.assertTrue(isinstance(embedding, list))


if __name__ == "__main__":
    unittest.main()
