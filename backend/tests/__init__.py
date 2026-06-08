"""Backend test suite for release confidence.

This module forcefully isolates test execution from local runtime .env values.
"""

import os
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
backend_root_text = str(BACKEND_ROOT)
if backend_root_text not in sys.path:
    sys.path.insert(0, backend_root_text)


# Force deterministic LLM behavior in tests regardless of local .env.
os.environ["LLM_PROVIDER"] = "template"
os.environ["LLM_ENABLE_REAL_CALLS"] = "false"
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["OPENROUTER_MODEL"] = "test-model"
os.environ["LLM_MAX_TOKENS"] = "500"
os.environ["LLM_TEMPERATURE"] = "0.2"
os.environ["LLM_TIMEOUT_SECONDS"] = "30"
os.environ["LLM_RETRY_ATTEMPTS"] = "0"
os.environ["LLM_RETRY_BACKOFF_SECONDS"] = "0"
os.environ["LLM_REQUEST_HARD_MAX_TOKENS"] = "2000"
os.environ["LLM_TASK_TOTAL_TOKEN_SOFT_LIMIT"] = "6000"
os.environ["LLM_TASK_TOTAL_TOKEN_HARD_LIMIT"] = "10000"
os.environ["LLM_ENABLE_COST_ESTIMATION"] = "true"
os.environ["RAG_ENABLED"] = "true"
os.environ["RAG_VECTOR_BACKEND"] = "local"
os.environ["EMBEDDING_DIMENSION"] = "64"
os.environ["RAG_TOP_K"] = "5"
os.environ["RAG_MIN_SCORE"] = "0.0"
os.environ["RAG_MAX_CONTEXT_CHARS"] = "4000"
os.environ["RAG_TRACE_SNIPPET_CHARS"] = "300"
os.environ["TASK_EXECUTION_MODE"] = "sync"
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "false"
os.environ["LOG_LEVEL"] = "INFO"
os.environ["ENABLE_REQUEST_LOGGING"] = "true"
os.environ["PORT"] = "8000"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-only-jwt-secret-minimum-32-chars"
os.environ["CORS_ORIGINS"] = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["RATE_LIMIT_REQUESTS_PER_MINUTE"] = "120"
os.environ["RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE"] = "20"
os.environ["RATE_LIMIT_TASK_EXECUTE_PER_MINUTE"] = "10"
os.environ["DOCUMENT_MAX_UPLOAD_MB"] = "5"
os.environ["DOCUMENT_ALLOWED_EXTENSIONS"] = ".txt,.md,.pdf"
os.environ["DOCUMENT_ALLOWED_MIME_TYPES"] = "text/plain,text/markdown,application/pdf"


def _refresh_loaded_settings_if_needed() -> None:
    config_module = sys.modules.get("app.core.config")
    if config_module is None:
        return

    if hasattr(config_module, "get_settings"):
        config_module.get_settings.cache_clear()
        config_module.settings = config_module.get_settings()

    llm_service_module = sys.modules.get("app.services.llm_service")
    if llm_service_module is not None:
        if hasattr(llm_service_module, "get_llm_service"):
            llm_service_module.get_llm_service.cache_clear()
        if hasattr(llm_service_module, "get_openai_client"):
            llm_service_module.get_openai_client.cache_clear()


_refresh_loaded_settings_if_needed()

from app.core.database import reset_test_schema

reset_test_schema()
