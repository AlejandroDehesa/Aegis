from __future__ import annotations

import unittest
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.task import TaskExecutionStepRead
from scripts.seed_demo_data import build_demo_task_templates


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


class SeedAndDevopsContractTests(unittest.TestCase):
    def test_demo_seed_generates_valid_trace_schema(self) -> None:
        templates = build_demo_task_templates(datetime.now(UTC))
        for template in templates:
            with self.subTest(title=template["title"]):
                trace = template.get("execution_trace", [])
                self.assertGreaterEqual(len(trace), 3)
                step_names = {step.get("step_name") for step in trace}
                self.assertIn("classification", step_names)
                self.assertIn("agent_selection", step_names)
                self.assertIn("execution", step_names)
                for step in trace:
                    TaskExecutionStepRead.model_validate(step)

    def test_seed_generates_professional_task_titles(self) -> None:
        templates = build_demo_task_templates(datetime.now(UTC))
        forbidden_titles = {"ns", "test", "tmp", "demo task"}
        for template in templates:
            title = str(template["title"]).strip().lower()
            self.assertGreaterEqual(len(title), 12)
            self.assertNotIn(title, forbidden_titles)

    def test_seed_covers_core_task_types_for_demo(self) -> None:
        templates = build_demo_task_templates(datetime.now(UTC))
        task_types = {template["task_type"] for template in templates}
        self.assertTrue({"comparison", "analysis", "planning", "summary", "research"}.issubset(task_types))

    def test_frontend_healthcheck_reports_healthy(self) -> None:
        compose_file = _find_repo_file("docker-compose.yml")
        if compose_file is None:
            self.skipTest("docker-compose.yml is not mounted in this test runtime")
        compose_content = compose_file.read_text(encoding="utf-8")
        self.assertIn("http://127.0.0.1/", compose_content)
        self.assertIn("wget -q --spider", compose_content)

    def test_env_files_are_ignored_in_gitignore(self) -> None:
        gitignore_file = _find_repo_file(".gitignore")
        if gitignore_file is None:
            self.skipTest(".gitignore is not mounted in this test runtime")
        gitignore_content = gitignore_file.read_text(encoding="utf-8")
        self.assertIn(".env", gitignore_content)
        self.assertIn("frontend/.env", gitignore_content)

    def test_readme_documents_seed_module_command(self) -> None:
        readme_file = _find_repo_file("README.md")
        if readme_file is None:
            self.skipTest("README.md is not mounted in this test runtime")
        readme_content = readme_file.read_text(encoding="utf-8")
        self.assertIn("python -m scripts.seed_demo_data", readme_content)

    def test_readme_documents_frontend_smoke_and_build(self) -> None:
        readme_file = _find_repo_file("README.md")
        if readme_file is None:
            self.skipTest("README.md is not mounted in this test runtime")
        readme_content = readme_file.read_text(encoding="utf-8")
        self.assertIn("npm run check:smoke", readme_content)
        self.assertIn("npm run build", readme_content)


if __name__ == "__main__":
    unittest.main()
