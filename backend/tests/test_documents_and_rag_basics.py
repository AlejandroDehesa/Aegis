from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import unittest
import uuid
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, UploadFile
from sqlalchemy.sql import Select

from app.api.v1.documents import get_documents, upload_document
from app.core.config import settings
from app.services.document_service import (
    DocumentValidationError,
    DOCUMENT_CONTENT_MAX_CHARS,
    DOCUMENT_TITLE_MAX_LENGTH,
    _chunk_text,
    _normalize_content,
    create_document,
    list_documents_for_user,
)
from app.services.retrieval_service import build_context, retrieve_relevant_chunks
from tests.helpers import FakeExecuteResult
from tests.helpers import build_user


class _FakeUpload:
    def __init__(self, filename: str, content_type: str, content: bytes) -> None:
        self.filename = filename
        self.content_type = content_type
        self._content = content

    async def read(self) -> bytes:
        return self._content


class DocumentsAndRagBasicsTests(unittest.TestCase):
    def test_document_upload_creates_chunks_or_controlled_fallback(self) -> None:
        chunks = _chunk_text(
            "FastAPI enables rapid API development with type hints and automatic docs. "
            "Django includes robust admin and built-in modules."
        )
        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(chunk.strip() for chunk in chunks))

    def test_chunk_text_returns_empty_for_blank_input(self) -> None:
        self.assertEqual(_chunk_text("   "), [])

    def test_chunk_text_respects_overlap_without_infinite_loop(self) -> None:
        long_text = " ".join(["token"] * 600)
        chunks = _chunk_text(long_text)
        self.assertGreater(len(chunks), 1)
        self.assertLess(len(chunks), 200)

    def test_normalize_content_strips_whitespace(self) -> None:
        self.assertEqual(_normalize_content("  hello world  "), "hello world")

    def test_create_document_rejects_empty_title(self) -> None:
        with self.assertRaises(DocumentValidationError):
            create_document(
                db=MagicMock(),
                user_id=uuid.uuid4(),
                title=" ",
                content="Some content",
                source_type="text",
            )

    def test_create_document_rejects_empty_content(self) -> None:
        with self.assertRaises(DocumentValidationError):
            create_document(
                db=MagicMock(),
                user_id=uuid.uuid4(),
                title="My document",
                content=" ",
                source_type="text",
            )

    def test_create_document_rejects_too_long_title(self) -> None:
        with self.assertRaises(DocumentValidationError):
            create_document(
                db=MagicMock(),
                user_id=uuid.uuid4(),
                title="x" * (DOCUMENT_TITLE_MAX_LENGTH + 1),
                content="Some content",
                source_type="text",
            )

    def test_create_document_rejects_too_long_content(self) -> None:
        with self.assertRaises(DocumentValidationError):
            create_document(
                db=MagicMock(),
                user_id=uuid.uuid4(),
                title="Valid title",
                content="x" * (DOCUMENT_CONTENT_MAX_CHARS + 1),
                source_type="text",
            )

    def test_upload_document_rejects_content_and_file_together(self) -> None:
        current_user = build_user()
        db = MagicMock()
        upload = UploadFile(filename="doc.txt", file=MagicMock())

        async def _run() -> None:
            with self.assertRaises(HTTPException) as context:
                await upload_document(
                    title="Combined input",
                    content="raw text",
                    file=upload,
                    current_user=current_user,
                    db=db,
                )
            self.assertEqual(context.exception.status_code, 400)

        asyncio.run(_run())

    def test_upload_document_rejects_empty_payload(self) -> None:
        current_user = build_user()
        db = MagicMock()

        async def _run() -> None:
            with self.assertRaises(HTTPException) as context:
                await upload_document(
                    title="No content",
                    content="",
                    file=None,
                    current_user=current_user,
                    db=db,
                )
            self.assertEqual(context.exception.status_code, 400)

        asyncio.run(_run())

    def test_upload_document_rejects_non_utf8_file(self) -> None:
        current_user = build_user()
        db = MagicMock()
        file_mock = MagicMock()
        file_mock.read = MagicMock(return_value=b"\xff\xfe\xfd")
        upload = UploadFile(filename="binary.bin", file=file_mock)

        async def _run() -> None:
            with self.assertRaises(HTTPException) as context:
                await upload_document(
                    title=None,
                    content=None,
                    file=upload,
                    current_user=current_user,
                    db=db,
                )
            self.assertEqual(context.exception.status_code, 400)

        asyncio.run(_run())

    def test_document_empty_upload_rejected(self) -> None:
        current_user = build_user()
        db = MagicMock()
        upload = _FakeUpload("empty.txt", "text/plain", b"")

        async def _run() -> None:
            with self.assertRaises(HTTPException) as context:
                await upload_document(
                    title=None,
                    content=None,
                    file=upload,  # type: ignore[arg-type]
                    current_user=current_user,
                    db=db,
                )
            self.assertEqual(context.exception.status_code, 400)

        asyncio.run(_run())

    def test_document_invalid_extension_rejected(self) -> None:
        current_user = build_user()
        db = MagicMock()
        upload = _FakeUpload("malware.exe", "application/octet-stream", b"fake")

        async def _run() -> None:
            with self.assertRaises(HTTPException) as context:
                await upload_document(
                    title=None,
                    content=None,
                    file=upload,  # type: ignore[arg-type]
                    current_user=current_user,
                    db=db,
                )
            self.assertEqual(context.exception.status_code, 400)

        asyncio.run(_run())

    def test_document_path_traversal_filename_sanitized_or_rejected(self) -> None:
        current_user = build_user()
        db = MagicMock()
        upload = _FakeUpload("../secrets.txt", "text/plain", b"hello")

        async def _run() -> None:
            with self.assertRaises(HTTPException) as context:
                await upload_document(
                    title=None,
                    content=None,
                    file=upload,  # type: ignore[arg-type]
                    current_user=current_user,
                    db=db,
                )
            self.assertEqual(context.exception.status_code, 400)

        asyncio.run(_run())

    def test_document_too_large_rejected(self) -> None:
        current_user = build_user()
        db = MagicMock()
        original_limit = settings.DOCUMENT_MAX_UPLOAD_MB
        settings.DOCUMENT_MAX_UPLOAD_MB = 1
        upload = _FakeUpload("large.txt", "text/plain", b"x" * (1024 * 1024 + 1))

        async def _run() -> None:
            with self.assertRaises(HTTPException) as context:
                await upload_document(
                    title=None,
                    content=None,
                    file=upload,  # type: ignore[arg-type]
                    current_user=current_user,
                    db=db,
                )
            self.assertEqual(context.exception.status_code, 400)

        try:
            asyncio.run(_run())
        finally:
            settings.DOCUMENT_MAX_UPLOAD_MB = original_limit

    def test_document_valid_txt_upload_still_works(self) -> None:
        current_user = build_user()
        db = MagicMock()
        upload = _FakeUpload("notes.txt", "text/plain", b"Useful architecture context")

        fake_document = MagicMock()
        fake_document.id = uuid.uuid4()
        fake_document.title = "notes.txt"
        fake_document.source_type = "file"
        fake_document.source_name = "notes.txt"
        fake_document.content = "Useful architecture context"
        fake_document.created_at = datetime.now(UTC)
        fake_document.chunks = [MagicMock(), MagicMock()]

        async def _run() -> None:
            with patch("app.api.v1.documents.create_document", return_value=fake_document):
                result = await upload_document(
                    title=None,
                    content=None,
                    file=upload,  # type: ignore[arg-type]
                    current_user=current_user,
                    db=db,
                )

            self.assertEqual(result.title, "notes.txt")
            self.assertEqual(result.source_type, "file")
            self.assertEqual(result.chunk_count, 2)

        asyncio.run(_run())

    def test_list_documents_service_applies_pagination_and_stable_order(self) -> None:
        db = MagicMock()
        user_id = uuid.uuid4()
        db.execute.return_value = FakeExecuteResult(scalar_values=[])

        list_documents_for_user(
            db=db,
            user_id=user_id,
            limit=10,
            offset=20,
        )

        query = db.execute.call_args[0][0]
        self.assertIsInstance(query, Select)
        query_text = str(query)
        self.assertIn("ORDER BY documents.created_at DESC, documents.id DESC", query_text)
        self.assertIn("LIMIT", query_text)
        self.assertIn("OFFSET", query_text)

    def test_get_documents_passes_limit_and_offset(self) -> None:
        current_user = build_user()
        db = MagicMock()

        with patch("app.api.v1.documents.list_documents_for_user", return_value=[] ) as list_mock:
            response = get_documents(
                limit=15,
                offset=30,
                current_user=current_user,
                db=db,
            )

        self.assertEqual(response, [])
        list_mock.assert_called_once_with(
            db=db,
            user_id=current_user.id,
            limit=15,
            offset=30,
        )

    def test_retrieve_relevant_chunks_returns_empty_for_blank_query(self) -> None:
        chunks = retrieve_relevant_chunks(query=" ", user_id=uuid.uuid4())
        self.assertEqual(chunks, [])

    def test_rag_fallback_does_not_crash_when_vector_store_unavailable(self) -> None:
        with (
            patch("app.services.retrieval_service.generate_embedding", return_value=[0.1, 0.2, 0.3]),
            patch("app.services.retrieval_service.query_records", return_value=[]),
        ):
            chunks = retrieve_relevant_chunks(
                query="compare docker deployment options",
                user_id=uuid.uuid4(),
                top_k=3,
                min_score=0.2,
            )
        self.assertEqual(chunks, [])

    def test_retrieve_relevant_chunks_filters_by_min_score(self) -> None:
        user_id = uuid.uuid4()
        with (
            patch("app.services.retrieval_service.generate_embedding", return_value=[0.1, 0.2]),
            patch(
                "app.services.retrieval_service.query_records",
                return_value=[
                    {
                        "id": "chunk-high",
                        "text": "high score chunk",
                        "metadata": {"document_title": "Doc A", "user_id": str(user_id)},
                        "score": 0.91,
                    },
                    {
                        "id": "chunk-low",
                        "text": "low score chunk",
                        "metadata": {"document_title": "Doc B", "user_id": str(user_id)},
                        "score": 0.05,
                    },
                ],
            ),
        ):
            chunks = retrieve_relevant_chunks(
                query="deployment",
                user_id=user_id,
                top_k=3,
                min_score=0.2,
            )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_id, "chunk-high")

    def test_build_context_returns_none_when_no_chunks(self) -> None:
        context = build_context([])
        self.assertIsNone(context.text)
        self.assertEqual(context.used_chunks, [])

    def test_build_context_marks_truncated_when_context_limit_small(self) -> None:
        from app.services.retrieval_service import RetrievedChunk

        chunks = [
            RetrievedChunk(
                chunk_id="1",
                document_id="doc-1",
                document_title="Doc",
                source_name="src",
                chunk_index=0,
                text="A" * 500,
                score=0.9,
            )
        ]
        context = build_context(chunks, max_chars=180)
        self.assertTrue(context.truncated)
        self.assertIsNotNone(context.text)


if __name__ == "__main__":
    unittest.main()
