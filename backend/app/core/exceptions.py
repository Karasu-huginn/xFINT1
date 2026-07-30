from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


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


def register_exception_handlers(application: FastAPI) -> None:
    """Attach the domain error handler to the given application."""
    application.add_exception_handler(DomainError, handle_domain_error)
