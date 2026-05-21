from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.document import DocumentChunk
from app.services.embeddings_service import generate_embeddings


BATCH_SIZE = 32


@dataclass
class BackfillSummary:
    scanned: int
    updated: int
    failed: int


def run_backfill(*, batch_size: int = BATCH_SIZE) -> BackfillSummary:
    scanned = 0
    updated = 0
    failed = 0

    while True:
        with SessionLocal() as session:
            chunks = session.execute(
                select(DocumentChunk)
                .where(DocumentChunk.embedding.is_(None))
                .order_by(DocumentChunk.created_at.asc())
                .limit(max(batch_size, 1))
            ).scalars().all()

            if not chunks:
                break

            scanned += len(chunks)
            texts = [chunk.content for chunk in chunks]

            try:
                embeddings = generate_embeddings(texts)
                if len(embeddings) != len(chunks):
                    raise ValueError("Embedding provider returned mismatched batch size.")

                for chunk, embedding in zip(chunks, embeddings, strict=True):
                    chunk.embedding = embedding

                session.commit()
                updated += len(chunks)
            except Exception:
                session.rollback()
                failed += len(chunks)
                break

    return BackfillSummary(scanned=scanned, updated=updated, failed=failed)


def main() -> None:
    summary = run_backfill()
    print(
        "PGVector backfill completed "
        f"(scanned={summary.scanned}, updated={summary.updated}, failed={summary.failed})."
    )


if __name__ == "__main__":
    main()
