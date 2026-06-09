from __future__ import annotations

import uuid

from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.http import REQUEST_ID_HEADER, build_error_payload


def _resolve_request_id(request: Request) -> str:
    from_state = getattr(request.state, "request_id", None)
    if isinstance(from_state, str) and from_state:
        return from_state
    from_header = request.headers.get(REQUEST_ID_HEADER)
    if from_header:
        return from_header
    return str(uuid.uuid4())


def register_exception_handlers(app: FastAPI) -> None:
    async def _http_error_response(
        request: Request,
        status_code: int,
        detail: object,
        headers: dict[str, str] | None = None,
    ) -> JSONResponse:
        request_id = _resolve_request_id(request)
        message = detail if isinstance(detail, str) else "Request failed."
        payload = build_error_payload(
            code=f"http_{status_code}",
            message=message,
            request_id=request_id,
            details=detail if not isinstance(detail, str) else None,
        )
        response = JSONResponse(status_code=status_code, content=payload, headers=headers)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return await _http_error_response(
            request=request,
            status_code=exc.status_code,
            detail=exc.detail,
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        return await _http_error_response(
            request=request,
            status_code=exc.status_code,
            detail=exc.detail,
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request_id = _resolve_request_id(request)
        payload = build_error_payload(
            code="validation_error",
            message="Request validation failed.",
            request_id=request_id,
            details=jsonable_encoder(exc.errors()),
        )
        response = JSONResponse(status_code=422, content=payload)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = _resolve_request_id(request)
        message = "Internal server error."
        details = None
        if settings.DEBUG:
            details = {"exception": str(exc)}
        payload = build_error_payload(
            code="internal_error",
            message=message,
            request_id=request_id,
            details=details,
        )
        response = JSONResponse(status_code=500, content=payload)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
