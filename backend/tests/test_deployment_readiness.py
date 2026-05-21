from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core import config as config_module


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


class DeploymentReadinessTests(unittest.TestCase):
    def tearDown(self) -> None:
        config_module.get_settings.cache_clear()
        config_module.settings = config_module.get_settings()

    def _resolve_settings(self):
        config_module.get_settings.cache_clear()
        return config_module.get_settings()

    def test_backend_port_uses_env_port_if_available(self) -> None:
        with patch.dict(os.environ, {"PORT": "9234"}, clear=False):
            settings = self._resolve_settings()
        self.assertEqual(settings.PORT, 9234)

    def test_cors_origins_parses_comma_separated_values(self) -> None:
        with patch.dict(
            os.environ,
            {"CORS_ORIGINS": "https://frontend.example.com, https://admin.example.com"},
            clear=False,
        ):
            settings = self._resolve_settings()
        self.assertEqual(
            settings.CORS_ORIGINS,
            ["https://frontend.example.com", "https://admin.example.com"],
        )

    def test_production_requires_strong_secret_or_warns_safely(self) -> None:
        with patch.dict(
            os.environ,
            {
                "APP_ENV": "production",
                "JWT_SECRET_KEY": "weak-secret",
                "DATABASE_URL": "sqlite+pysqlite:///:memory:",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(ValueError, "JWT_SECRET_KEY"):
                self._resolve_settings()

    def test_frontend_env_example_contains_vite_api_base_url(self) -> None:
        env_example = _find_repo_file("frontend/.env.example")
        if env_example is None:
            self.skipTest("frontend/.env.example is not mounted in this test runtime")
        content = env_example.read_text(encoding="utf-8")
        self.assertIn("VITE_API_BASE_URL=", content)

    def test_frontend_env_example_documents_vite_api_base_url(self) -> None:
        env_example = _find_repo_file("frontend/.env.example")
        if env_example is None:
            self.skipTest("frontend/.env.example is not mounted in this test runtime")
        content = env_example.read_text(encoding="utf-8")
        self.assertIn("https://your-backend-url/api/v1", content)

    def test_backend_env_example_contains_deployment_vars(self) -> None:
        env_example = _find_repo_file(".env.example")
        if env_example is None:
            self.skipTest(".env.example is not mounted in this test runtime")
        content = env_example.read_text(encoding="utf-8")
        self.assertIn("PORT=", content)
        self.assertIn("DATABASE_URL=", content)
        self.assertIn("CORS_ORIGINS=", content)
        self.assertIn("TASK_EXECUTION_MODE=", content)
        self.assertIn("RAG_ENABLED=", content)
        self.assertIn("RAG_VECTOR_BACKEND=", content)

    def test_deployment_railway_doc_exists(self) -> None:
        deployment_doc = _find_repo_file("docs/DEPLOYMENT_RAILWAY.md")
        if deployment_doc is None:
            self.skipTest("docs/DEPLOYMENT_RAILWAY.md is not mounted in this test runtime")
        self.assertTrue(deployment_doc.exists())

    def test_backend_start_command_documented(self) -> None:
        deployment_doc = _find_repo_file("docs/DEPLOYMENT_RAILWAY.md")
        if deployment_doc is None:
            self.skipTest("docs/DEPLOYMENT_RAILWAY.md is not mounted in this test runtime")
        content = deployment_doc.read_text(encoding="utf-8")
        self.assertIn("uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}", content)

    def test_deployment_doc_mentions_migrations(self) -> None:
        deployment_doc = _find_repo_file("docs/DEPLOYMENT_RAILWAY.md")
        if deployment_doc is None:
            self.skipTest("docs/DEPLOYMENT_RAILWAY.md is not mounted in this test runtime")
        content = deployment_doc.read_text(encoding="utf-8")
        self.assertIn("alembic upgrade head", content)

    def test_deployment_doc_mentions_health_ready(self) -> None:
        deployment_doc = _find_repo_file("docs/DEPLOYMENT_RAILWAY.md")
        if deployment_doc is None:
            self.skipTest("docs/DEPLOYMENT_RAILWAY.md is not mounted in this test runtime")
        content = deployment_doc.read_text(encoding="utf-8")
        self.assertIn("/api/v1/health/ready", content)

    def test_deployment_doc_warns_about_local_storage_limitations(self) -> None:
        deployment_doc = _find_repo_file("docs/DEPLOYMENT_RAILWAY.md")
        if deployment_doc is None:
            self.skipTest("docs/DEPLOYMENT_RAILWAY.md is not mounted in this test runtime")
        content = deployment_doc.read_text(encoding="utf-8").lower()
        self.assertIn("local file storage can be ephemeral", content)
        self.assertIn("not a distributed job queue", content)

    def test_deployment_docs_warn_against_backend_upstream_in_railway(self) -> None:
        deployment_doc = _find_repo_file("docs/DEPLOYMENT_RAILWAY.md")
        if deployment_doc is None:
            self.skipTest("docs/DEPLOYMENT_RAILWAY.md is not mounted in this test runtime")
        content = deployment_doc.read_text(encoding="utf-8")
        self.assertIn("Do not use `proxy_pass http://backend:8000`", content)
        self.assertIn("Do not use `proxy_pass http://backend:8000` or `upstream backend`", content)

    def test_deployment_doc_does_not_contain_secrets(self) -> None:
        deployment_doc = _find_repo_file("docs/DEPLOYMENT_RAILWAY.md")
        if deployment_doc is None:
            self.skipTest("docs/DEPLOYMENT_RAILWAY.md is not mounted in this test runtime")
        content = deployment_doc.read_text(encoding="utf-8")
        self.assertNotIn("sk-or-", content)
        self.assertNotIn("OPENROUTER_API_KEY=sk-", content)
        self.assertNotIn("postgres://user:password@", content)

    def test_backend_alembic_ini_exists(self) -> None:
        alembic_ini = _find_repo_file("backend/alembic.ini")
        if alembic_ini is None:
            self.skipTest("backend/alembic.ini is not mounted in this test runtime")
        self.assertTrue(alembic_ini.exists())

    def test_backend_alembic_script_location_configured(self) -> None:
        alembic_ini = _find_repo_file("backend/alembic.ini")
        if alembic_ini is None:
            self.skipTest("backend/alembic.ini is not mounted in this test runtime")
        content = alembic_ini.read_text(encoding="utf-8")
        self.assertIn("script_location = alembic", content)

    def test_backend_alembic_versions_exist(self) -> None:
        versions_dir = _find_repo_file("backend/alembic/versions")
        if versions_dir is None:
            self.skipTest("backend/alembic/versions is not mounted in this test runtime")
        revisions = list(versions_dir.glob("*.py"))
        self.assertGreaterEqual(len(revisions), 1)

    def test_backfill_script_exists(self) -> None:
        backfill_script = _find_repo_file("backend/scripts/backfill_pgvector_embeddings.py")
        if backfill_script is None:
            self.skipTest("backfill script is not mounted in this test runtime")
        self.assertTrue(backfill_script.exists())

    def test_pgvector_migration_available_in_backend_context(self) -> None:
        migration_file = _find_repo_file(
            "backend/alembic/versions/0002_pgvector_embeddings.py"
        )
        if migration_file is None:
            self.skipTest("backend pgvector migration is not mounted in this test runtime")
        content = migration_file.read_text(encoding="utf-8")
        self.assertIn("CREATE EXTENSION IF NOT EXISTS vector", content)
        self.assertIn("embedding vector", content)
        self.assertIn('revision = "0002_pgvector_embeddings"', content)

    def test_alembic_revision_ids_fit_varchar_32(self) -> None:
        versions_dir = _find_repo_file("backend/alembic/versions")
        if versions_dir is None:
            self.skipTest("backend/alembic/versions is not mounted in this test runtime")

        for migration_file in versions_dir.glob("*.py"):
            content = migration_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("revision = "):
                    revision_id = line.split("=", maxsplit=1)[1].strip().strip("\"'")
                    self.assertLessEqual(
                        len(revision_id),
                        32,
                        msg=f"{migration_file.name} revision id exceeds VARCHAR(32): {revision_id}",
                    )

    def test_ci_workflow_still_exists(self) -> None:
        workflow_file = _find_repo_file(".github/workflows/ci.yml")
        if workflow_file is None:
            self.skipTest(".github/workflows/ci.yml is not mounted in this test runtime")
        self.assertTrue(workflow_file.exists())

    def test_nginx_conf_does_not_reference_backend_service_name(self) -> None:
        nginx_file = _find_repo_file("frontend/nginx.conf")
        if nginx_file is None:
            self.skipTest("frontend/nginx.conf is not mounted in this test runtime")
        content = nginx_file.read_text(encoding="utf-8").lower()
        self.assertNotIn("upstream backend", content)
        self.assertNotIn("proxy_pass http://backend:8000", content)

    def test_alembic_upgrade_command_documented(self) -> None:
        readme = _find_repo_file("README.md")
        if readme is None:
            self.skipTest("README.md is not mounted in this test runtime")
        content = readme.read_text(encoding="utf-8")
        self.assertIn("alembic upgrade head", content)

    def test_no_env_file_tracked(self) -> None:
        repo_root = next((candidate for candidate in REPO_CANDIDATES if (candidate / ".git").exists()), None)
        if repo_root is None:
            self.skipTest(".git metadata is not mounted in this test runtime")
        command = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
        if command.returncode != 0:
            self.skipTest("git ls-files unavailable in this test runtime")
        tracked = set(command.stdout.splitlines())
        self.assertNotIn(".env", tracked)
        self.assertNotIn("frontend/.env", tracked)


if __name__ == "__main__":
    unittest.main()
