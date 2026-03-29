"""Custom exceptions and FastAPI exception handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.models.status import ErrorResponse


class JokeTellerError(Exception):
    """Base application exception with a user-friendly payload."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        suggestion: str | None = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        self.code = code
        self.message = message
        self.suggestion = suggestion
        self.status_code = status_code
        super().__init__(message)

    def to_response(self) -> JSONResponse:
        """Convert the exception into a structured JSON response."""

        payload = ErrorResponse(
            code=self.code,
            message=self.message,
            suggestion=self.suggestion,
        )
        return JSONResponse(status_code=self.status_code, content=payload.model_dump())

    def to_payload(self) -> dict[str, Any]:
        """Convert the exception into a plain JSON-serializable payload."""

        return ErrorResponse(
            code=self.code,
            message=self.message,
            suggestion=self.suggestion,
        ).model_dump()


class LMStudioUnavailableError(JokeTellerError):
    """Raised when LM Studio cannot be reached."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        super().__init__(
            code="lm_studio_unavailable",
            message=message,
            suggestion=suggestion
            or "Make sure LM Studio is running locally and the local server is enabled.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class LMStudioTimeoutError(JokeTellerError):
    """Raised when LM Studio takes too long to respond."""

    def __init__(self) -> None:
        super().__init__(
            code="lm_studio_timeout",
            message="LM Studio took too long to respond.",
            suggestion="Try again, lower max tokens, or choose a faster local model.",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


class InvalidModelError(JokeTellerError):
    """Raised when the requested model is missing or unavailable."""

    def __init__(self, message: str, suggestion: str | None = None) -> None:
        super().__init__(
            code="invalid_model",
            message=message,
            suggestion=suggestion or "Load a model in LM Studio or choose a valid model name.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class EmptyModelResponseError(JokeTellerError):
    """Raised when the upstream model returns no text."""

    def __init__(self) -> None:
        super().__init__(
            code="empty_model_response",
            message="The model returned an empty response.",
            suggestion="Try again or adjust the prompt and generation settings.",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class UpstreamProtocolError(JokeTellerError):
    """Raised when the upstream response shape is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(
            code="upstream_protocol_error",
            message=message,
            suggestion="Check that LM Studio is exposing an OpenAI-compatible local API.",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


def _validation_error_to_message(exc: RequestValidationError) -> str:
    """Summarize the first validation error in plain language."""

    first_error = exc.errors()[0] if exc.errors() else None
    if not first_error:
        return "The request payload is invalid."
    location = " -> ".join(str(item) for item in first_error.get("loc", []))
    detail = first_error.get("msg", "Invalid value.")
    return f"Invalid request field `{location}`. {detail}"


def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom and framework-level exception handlers."""

    @app.exception_handler(JokeTellerError)
    async def handle_joke_teller_error(_: Any, exc: JokeTellerError) -> JSONResponse:
        return exc.to_response()

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Any, exc: RequestValidationError) -> JSONResponse:
        payload = ErrorResponse(
            code="invalid_request",
            message=_validation_error_to_message(exc),
            suggestion="Review the request payload and try again.",
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Any, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        payload = ErrorResponse(code="http_error", message=message, suggestion=None)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Any, exc: Exception) -> JSONResponse:
        payload = ErrorResponse(
            code="internal_error",
            message="Something unexpected happened inside JokeTeller.",
            suggestion="Check the backend logs and try again.",
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(),
        )

