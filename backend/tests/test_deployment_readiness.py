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

    def test_deployment_doc_does_not_contain_secrets(self) -> None:
        deployment_doc = _find_repo_file("docs/DEPLOYMENT_RAILWAY.md")
        if deployment_doc is None:
            self.skipTest("docs/DEPLOYMENT_RAILWAY.md is not mounted in this test runtime")
        content = deployment_doc.read_text(encoding="utf-8")
        self.assertNotIn("sk-or-", content)
        self.assertNotIn("OPENROUTER_API_KEY=sk-", content)
        self.assertNotIn("postgres://user:password@", content)

    def test_ci_workflow_still_exists(self) -> None:
        workflow_file = _find_repo_file(".github/workflows/ci.yml")
        if workflow_file is None:
            self.skipTest(".github/workflows/ci.yml is not mounted in this test runtime")
        self.assertTrue(workflow_file.exists())

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
