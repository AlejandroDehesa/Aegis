from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


REQUEST_ID_HEADER = "X-Request-ID"
LOGGER_NAME = "aegis.http"


def get_request_id(request: Request) -> str:
    existing = request.headers.get(REQUEST_ID_HEADER)
    if existing:
        return existing.strip()[:128]
    return str(uuid.uuid4())


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def build_error_payload(
    *,
    code: str,
    message: str,
    request_id: str,
    details: object | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    details: object | None = None,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status_code,
        content=build_error_payload(
            code=code,
            message=message,
            request_id=request_id,
            details=details,
        ),
    )
    response.headers[REQUEST_ID_HEADER] = request_id
    return response


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_epoch_seconds: int


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._buckets: dict[tuple[str, int], int] = {}

    def check(
        self,
        *,
        key: str,
        limit: int,
        now: float | None = None,
    ) -> RateLimitResult:
        if limit <= 0:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_epoch_seconds=int(time.time()) + 60,
            )

        current = now if now is not None else time.time()
        minute_window = int(current // 60)
        reset_epoch_seconds = (minute_window + 1) * 60
        bucket_key = (key, minute_window)

        with self._lock:
            current_count = self._buckets.get(bucket_key, 0)
            if current_count >= limit:
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_epoch_seconds=reset_epoch_seconds,
                )

            next_count = current_count + 1
            self._buckets[bucket_key] = next_count
            remaining = max(limit - next_count, 0)
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_epoch_seconds=reset_epoch_seconds,
            )


TASK_EXECUTE_PATH_PATTERN = re.compile(r"^/api/v1/tasks/[^/]+/execute$")


def _resolve_rate_limit(path: str) -> tuple[str, int] | None:
    normalized = path.rstrip("/") or "/"
    if normalized in {"/api/v1/health", "/api/v1/health/live", "/api/v1/health/ready"}:
        return None
    if normalized in {"/api/v1/login", "/api/v1/signup"}:
        return ("auth", settings.RATE_LIMIT_AUTH_REQUESTS_PER_MINUTE)
    if TASK_EXECUTE_PATH_PATTERN.match(normalized):
        return ("task_execute", settings.RATE_LIMIT_TASK_EXECUTE_PER_MINUTE)
    return (normalized, settings.RATE_LIMIT_REQUESTS_PER_MINUTE)


rate_limiter = InMemoryRateLimiter()


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._logger = logging.getLogger(LOGGER_NAME)

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        started_at = time.perf_counter()
        request_id = get_request_id(request)
        request.state.request_id = request_id

        if settings.RATE_LIMIT_ENABLED:
            limit_config = _resolve_rate_limit(request.url.path)
            if limit_config is not None:
                scope, limit = limit_config
                limit_key = f"{get_client_ip(request)}:{scope}"
                result = rate_limiter.check(key=limit_key, limit=limit)
                if not result.allowed:
                    return error_response(
                        status_code=429,
                        code="rate_limit_exceeded",
                        message="Rate limit exceeded. Please retry later.",
                        request_id=request_id,
                        details={
                            "limit": result.limit,
                            "remaining": result.remaining,
                            "reset_epoch_seconds": result.reset_epoch_seconds,
                        },
                    )

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id

        if settings.ENABLE_REQUEST_LOGGING:
            duration_ms = max(int((time.perf_counter() - started_at) * 1000), 0)
            self._logger.info(
                json.dumps(
                    {
                        "event": "request_completed",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                        "client_ip": get_client_ip(request),
                    }
                )
            )

        return response
