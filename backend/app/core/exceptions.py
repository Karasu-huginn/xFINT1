import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Base class for business-rule failures raised by service functions."""

    status_code = 400
    code = "domain_error"

    def __init__(self, message: str) -> None:
        """Store the human-readable message carried to the client."""
        super().__init__(message)
        self.message = message


class ValidationFailedError(DomainError):
    """Raised when input passes schema checks but breaks a business rule."""

    status_code = 400
    code = "validation_failed"


class AuthenticationError(DomainError):
    """Raised when credentials are absent, invalid or expired."""

    status_code = 401
    code = "authentication_failed"


class PermissionDeniedError(DomainError):
    """Raised when an authenticated caller lacks the required role."""

    status_code = 403
    code = "permission_denied"


class NotFoundError(DomainError):
    """Raised when a resource is absent or invisible to the caller."""

    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    """Raised when an action collides with existing state."""

    status_code = 409
    code = "conflict"


async def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
    """Translate any domain error into its documented HTTP response."""
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.message, "code": error.code},
    )


async def handle_validation_error(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    """Flatten Pydantic validation errors into a single readable detail string."""
    errors = error.errors()
    if not errors:
        detail = "Validation failed"
    else:
        first_error = errors[0]
        field_path = " > ".join(str(loc) for loc in first_error["loc"][1:])
        msg = first_error.get("msg", "Invalid value")
        detail = f"{field_path}: {msg}" if field_path else msg
    return JSONResponse(
        status_code=422,
        content={"detail": detail, "code": "validation_error"},
    )


async def handle_http_exception(
    request: Request, error: StarletteHTTPException
) -> JSONResponse:
    """Translate Starlette HTTP exceptions into uniform error responses."""
    return JSONResponse(
        status_code=error.status_code,
        content={"detail": error.detail, "code": "http_error"},
    )


async def handle_unhandled_exception(
    request: Request, error: Exception
) -> JSONResponse:
    """Log unhandled exceptions and return a safe error response."""
    logger.error("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error"},
    )


def register_exception_handlers(application: FastAPI) -> None:
    """Attach all error handlers to the given application."""
    application.add_exception_handler(DomainError, handle_domain_error)
    application.add_exception_handler(
        RequestValidationError, handle_validation_error
    )
    application.add_exception_handler(
        StarletteHTTPException, handle_http_exception
    )
    application.add_exception_handler(Exception, handle_unhandled_exception)
