from __future__ import annotations

import unittest
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.http import rate_limiter
from app.main import app


def _ensure_unhandled_test_route() -> None:
    if any(getattr(route, "path", "") == "/api/v1/_test/unhandled" for route in app.routes):
        return

    def _raise_unhandled() -> dict[str, str]:
        raise RuntimeError("Sensitive traceback detail should not leak.")

    app.add_api_route("/api/v1/_test/unhandled", _raise_unhandled, methods=["GET"])


class ApiHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self._original_rate_limit_enabled = settings.RATE_LIMIT_ENABLED
        self._original_rate_limit_general = settings.RATE_LIMIT_REQUESTS_PER_MINUTE
        self._original_rate_limit_auth = settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE
        self._original_rate_limit_execute = settings.RATE_LIMIT_TASK_EXECUTE_PER_MINUTE
        self._original_logging = settings.ENABLE_REQUEST_LOGGING
        rate_limiter._buckets.clear()
        _ensure_unhandled_test_route()

    def tearDown(self) -> None:
        settings.RATE_LIMIT_ENABLED = self._original_rate_limit_enabled
        settings.RATE_LIMIT_REQUESTS_PER_MINUTE = self._original_rate_limit_general
        settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE = self._original_rate_limit_auth
        settings.RATE_LIMIT_TASK_EXECUTE_PER_MINUTE = self._original_rate_limit_execute
        settings.ENABLE_REQUEST_LOGGING = self._original_logging
        rate_limiter._buckets.clear()

    def test_request_id_header_is_added(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/v1/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers.get("X-Request-ID"))

    def test_security_headers_are_added(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/v1/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(response.headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(
            response.headers.get("Referrer-Policy"),
            "strict-origin-when-cross-origin",
        )
        self.assertEqual(
            response.headers.get("Permissions-Policy"),
            "geolocation=(), microphone=(), camera=()",
        )

    def test_request_id_header_is_preserved(self) -> None:
        expected_id = "req-explicit-id"
        with TestClient(app) as client:
            response = client.get("/api/v1/health/live", headers={"X-Request-ID": expected_id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("X-Request-ID"), expected_id)

    def test_error_response_contains_request_id(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/v1/does-not-exist")
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertIn("error", payload)
        self.assertTrue(payload["error"].get("request_id"))

    def test_validation_error_has_consistent_shape(self) -> None:
        with TestClient(app) as client:
            response = client.post("/api/v1/signup", json={})
        self.assertEqual(response.status_code, 422)
        payload = response.json()
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["code"], "validation_error")
        self.assertEqual(payload["error"]["message"], "Request validation failed.")
        self.assertIsInstance(payload["error"].get("details"), list)

    def test_unhandled_exception_does_not_expose_stacktrace(self) -> None:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/_test/unhandled")
        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertIn("error", payload)
        self.assertEqual(payload["error"]["code"], "internal_error")
        self.assertNotIn("traceback", str(payload).lower())
        self.assertNotIn("Sensitive traceback detail should not leak.", str(payload))

    def test_health_live_ok(self) -> None:
        with TestClient(app) as client:
            response = client.get("/api/v1/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_health_ready_checks_database(self) -> None:
        with TestClient(app) as client:
            with patch("app.api.v1.health.check_database_connection", return_value=True):
                ok_response = client.get("/api/v1/health/ready")
            with patch("app.api.v1.health.check_database_connection", return_value=False):
                failed_response = client.get("/api/v1/health/ready")

        self.assertEqual(ok_response.status_code, 200)
        self.assertEqual(ok_response.json()["status"], "ready")
        self.assertEqual(failed_response.status_code, 503)
        self.assertEqual(failed_response.json()["status"], "not_ready")

    def test_health_ready_does_not_call_openrouter(self) -> None:
        with TestClient(app) as client:
            with patch(
                "app.services.llm.providers.openrouter_provider.OpenRouterProvider.generate",
                side_effect=RuntimeError("should not be called"),
            ) as openrouter_call:
                response = client.get("/api/v1/health/ready")
        self.assertIn(response.status_code, {200, 503})
        openrouter_call.assert_not_called()

    def test_rate_limit_can_be_disabled(self) -> None:
        settings.RATE_LIMIT_ENABLED = False
        with TestClient(app) as client:
            responses = [client.get("/api/v1/agents") for _ in range(6)]
        self.assertTrue(all(resp.status_code == 200 for resp in responses))

    def test_rate_limit_blocks_after_limit(self) -> None:
        settings.RATE_LIMIT_ENABLED = True
        settings.RATE_LIMIT_REQUESTS_PER_MINUTE = 2
        settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE = 10
        settings.RATE_LIMIT_TASK_EXECUTE_PER_MINUTE = 10

        with TestClient(app) as client:
            first = client.get("/api/v1/agents")
            second = client.get("/api/v1/agents")
            third = client.get("/api/v1/agents")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 429)
        self.assertEqual(third.json()["error"]["code"], "rate_limit_exceeded")

    def test_auth_rate_limit_is_stricter_than_general_if_applicable(self) -> None:
        settings.RATE_LIMIT_ENABLED = True
        settings.RATE_LIMIT_REQUESTS_PER_MINUTE = 5
        settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE = 2
        settings.RATE_LIMIT_TASK_EXECUTE_PER_MINUTE = 10

        with TestClient(app) as client:
            auth_attempt_1 = client.post(
                "/api/v1/login",
                json={"email": "none@example.com", "password": "badpass123"},
            )
            auth_attempt_2 = client.post(
                "/api/v1/login",
                json={"email": "none@example.com", "password": "badpass123"},
            )
            auth_attempt_3 = client.post(
                "/api/v1/login",
                json={"email": "none@example.com", "password": "badpass123"},
            )
            general = client.get("/api/v1/agents")

        self.assertEqual(auth_attempt_1.status_code, 401)
        self.assertEqual(auth_attempt_2.status_code, 401)
        self.assertEqual(auth_attempt_3.status_code, 429)
        self.assertEqual(general.status_code, 200)

    def test_no_authorization_header_in_request_logs(self) -> None:
        settings.ENABLE_REQUEST_LOGGING = True
        with self.assertLogs("aegis.http", level="INFO") as log_context:
            with TestClient(app) as client:
                response = client.get(
                    "/api/v1/health/live",
                    headers={"Authorization": "Bearer super-secret-token"},
                )
        self.assertEqual(response.status_code, 200)
        merged_logs = "\n".join(log_context.output)
        self.assertNotIn("Authorization", merged_logs)
        self.assertNotIn("super-secret-token", merged_logs)

    def test_execute_task_requires_auth(self) -> None:
        task_id = uuid.uuid4()
        with TestClient(app) as client:
            response = client.post(f"/api/v1/tasks/{task_id}/execute")
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
