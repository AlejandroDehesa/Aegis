"""Backend test suite for release confidence.

This module forcefully isolates test execution from local runtime .env values.
"""

import os
import sys


# Force deterministic LLM behavior in tests regardless of local .env.
os.environ["LLM_PROVIDER"] = "template"
os.environ["LLM_ENABLE_REAL_CALLS"] = "false"
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["OPENROUTER_MODEL"] = "test-model"
os.environ["LLM_MAX_TOKENS"] = "500"
os.environ["LLM_TEMPERATURE"] = "0.2"
os.environ["LLM_TIMEOUT_SECONDS"] = "30"


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
