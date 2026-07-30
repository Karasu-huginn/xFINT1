import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationFailedError,
    register_exception_handlers,
)


async def raise_domain_error(kind: str) -> None:
    """Raise the domain error named in the path."""
    errors = {
        "notfound": NotFoundError("Report not found"),
        "denied": PermissionDeniedError("Managers only"),
        "conflict": ConflictError("Email already registered"),
        "validation": ValidationFailedError("Amount must be positive"),
        "auth": AuthenticationError("Invalid credentials"),
    }
    raise errors[kind]


async def raise_http_exception(kind: str) -> None:
    """Raise an HTTPException."""
    raise HTTPException(status_code=404, detail="Resource not found")


async def raise_unhandled_exception() -> None:
    """Raise an unhandled exception to test 500 handler."""
    raise RuntimeError("Something went wrong")


class RequestPayload(BaseModel):
    """Schema with validation."""

    amount: int = Field(..., gt=0)


async def validate_request(payload: RequestPayload) -> dict[str, int]:
    """Receive a validated request payload."""
    return {"amount": payload.amount}


@pytest.fixture
def failing_client():
    """Return a client for a throwaway app whose route raises a domain error."""
    application = FastAPI()
    register_exception_handlers(application)
    application.add_api_route("/boom/{kind}", raise_domain_error, methods=["GET"])
    application.add_api_route(
        "/http/{kind}", raise_http_exception, methods=["GET"]
    )
    application.add_api_route(
        "/unhandled", raise_unhandled_exception, methods=["GET"]
    )
    application.add_api_route(
        "/validate", validate_request, methods=["POST"]
    )
    return TestClient(application)


@pytest.fixture
def failing_client_no_raise():
    """Return a client with raise_server_exceptions=False for 500 testing."""
    application = FastAPI()
    register_exception_handlers(application)
    application.add_api_route(
        "/unhandled", raise_unhandled_exception, methods=["GET"]
    )
    return TestClient(application, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("kind", "expected_status", "expected_code", "expected_detail"),
    [
        ("notfound", 404, "not_found", "Report not found"),
        ("denied", 403, "permission_denied", "Managers only"),
        ("conflict", 409, "conflict", "Email already registered"),
        ("validation", 400, "validation_failed", "Amount must be positive"),
        ("auth", 401, "authentication_failed", "Invalid credentials"),
    ],
)
def test_domain_errors_map_to_status_codes(
    failing_client, kind, expected_status, expected_code, expected_detail
):
    """Each domain error becomes its documented status code and error code."""
    response = failing_client.get(f"/boom/{kind}")
    assert response.status_code == expected_status
    assert response.json()["code"] == expected_code
    assert response.json()["detail"] == expected_detail


def test_http_exception_returns_uniform_error_format(failing_client):
    """HTTPException is translated to uniform error format."""
    response = failing_client.get("/http/any")
    assert response.status_code == 404
    assert response.json()["code"] == "http_error"
    assert response.json()["detail"] == "Resource not found"


def test_validation_error_returns_flat_string_detail(failing_client):
    """Pydantic validation errors are flattened into a string detail."""
    response = failing_client.post("/validate", json={"amount": -1})
    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert isinstance(response.json()["detail"], str)
    assert "amount" in response.json()["detail"].lower()


def test_unhandled_exception_returns_safe_error(failing_client_no_raise):
    """Unhandled exceptions return 500 without exposing the exception message."""
    response = failing_client_no_raise.get("/unhandled")
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert response.json()["detail"] == "Internal server error"
    assert "RuntimeError" not in response.json()["detail"]
    assert "Something went wrong" not in response.json()["detail"]


def test_http_exception_preserves_headers(failing_client):
    """HTTPException headers (e.g. Allow) are preserved in the response."""
    response = failing_client.post("/validate", json={"amount": 1})
    assert response.status_code == 200
    response = failing_client.post("/boom/notfound")
    assert response.status_code == 405
    assert "Allow" in response.headers
