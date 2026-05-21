"""init_pgvector_rag.py — One-shot RAG initialisation for Railway deploys.

Run order:
  1. Apply all pending Alembic migrations (idempotent — safe to re-run).
  2. Backfill embeddings for any DocumentChunk rows that are missing them.
  3. Print a verification summary so the deploy log confirms success.

Usage (from repo root):
    cd backend && python -m scripts.init_pgvector_rag

Or as a Railway start-command pre-hook:
    python -m scripts.init_pgvector_rag && uvicorn app.main:app ...
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy import text

from app.core.database import SessionLocal, create_tables
from scripts.backfill_pgvector_embeddings import run_backfill


# ---------------------------------------------------------------------------
# Step 1 — Alembic migrations
# ---------------------------------------------------------------------------

def _run_alembic_upgrade() -> None:
    """Run ``alembic upgrade head`` from the repository root.

    The alembic.ini lives at the repo root (one level above ``backend/``),
    so we resolve that path dynamically rather than hard-coding it.
    """
    backend_dir = Path(__file__).resolve().parent.parent  # .../backend
    repo_root = backend_dir.parent                         # .../repo-root

    alembic_ini = repo_root / "alembic.ini"
    if not alembic_ini.exists():
        print(
            f"[init_pgvector_rag] WARNING: alembic.ini not found at {alembic_ini}. "
            "Skipping Alembic migration step — schema will be managed by create_tables()."
        )
        return

    print("[init_pgvector_rag] Running: alembic upgrade head …")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(alembic_ini), "upgrade", "head"],
        cwd=str(repo_root),
        capture_output=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed with exit code {result.returncode}. "
            "Check the output above for details."
        )
    print("[init_pgvector_rag] Alembic migrations applied successfully.")


# ---------------------------------------------------------------------------
# Step 2 — Ensure tables exist (fallback when Alembic is skipped)
# ---------------------------------------------------------------------------

def _ensure_schema() -> None:
    """Create tables via SQLAlchemy metadata if they do not already exist.

    This is a safety net for environments where Alembic is not available or
    the alembic.ini is not mounted (e.g. minimal CI containers).
    """
    print("[init_pgvector_rag] Ensuring database schema is up to date …")
    create_tables()
    print("[init_pgvector_rag] Schema check complete.")


# ---------------------------------------------------------------------------
# Step 3 — Backfill missing embeddings
# ---------------------------------------------------------------------------

def _run_backfill() -> None:
    print("[init_pgvector_rag] Starting embedding backfill …")
    summary = run_backfill()
    print(
        f"[init_pgvector_rag] Backfill complete — "
        f"scanned={summary.scanned}, updated={summary.updated}, failed={summary.failed}."
    )
    if summary.failed > 0:
        print(
            f"[init_pgvector_rag] WARNING: {summary.failed} chunk(s) could not be embedded. "
            "RAG will still work for chunks that were successfully embedded."
        )


# ---------------------------------------------------------------------------
# Step 4 — Verification
# ---------------------------------------------------------------------------

def _verify() -> None:
    """Print a quick sanity-check summary to the deploy log."""
    print("[init_pgvector_rag] Verifying pgvector setup …")

    with SessionLocal() as session:
        total_chunks: int = session.execute(
            text("SELECT COUNT(*) FROM document_chunks")
        ).scalar_one()

        embedded_chunks: int = session.execute(
            text("SELECT COUNT(*) FROM document_chunks WHERE embedding IS NOT NULL")
        ).scalar_one()

        # Check that the pgvector extension is installed.
        pgvector_installed: bool = bool(
            session.execute(
                text(
                    "SELECT 1 FROM pg_extension WHERE extname = 'vector' LIMIT 1"
                )
            ).scalar_one_or_none()
        )

    coverage = (
        f"{embedded_chunks}/{total_chunks}"
        f" ({100 * embedded_chunks // total_chunks if total_chunks else 0}%)"
    )

    print(f"[init_pgvector_rag]   pgvector extension installed : {pgvector_installed}")
    print(f"[init_pgvector_rag]   chunks with embeddings       : {coverage}")

    if not pgvector_installed:
        print(
            "[init_pgvector_rag] ERROR: pgvector extension is NOT installed. "
            "Run 'CREATE EXTENSION IF NOT EXISTS vector;' on your PostgreSQL instance."
        )
        sys.exit(1)

    print("[init_pgvector_rag] Verification passed. RAG is ready.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("[init_pgvector_rag] === pgvector RAG initialisation starting ===")

    try:
        _run_alembic_upgrade()
    except RuntimeError as error:
        print(f"[init_pgvector_rag] Alembic step failed: {error}")
        print("[init_pgvector_rag] Falling back to create_tables() …")

    _ensure_schema()
    _run_backfill()
    _verify()

    print("[init_pgvector_rag] === Initialisation complete ===")


if __name__ == "__main__":
    main()
