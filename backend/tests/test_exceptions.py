import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    register_exception_handlers,
)


async def raise_domain_error(kind: str) -> None:
    """Raise the domain error named in the path."""
    errors = {
        "notfound": NotFoundError("Report not found"),
        "denied": PermissionDeniedError("Managers only"),
        "conflict": ConflictError("Email already registered"),
    }
    raise errors[kind]


@pytest.fixture
def failing_client():
    """Return a client for a throwaway app whose route raises a domain error."""
    application = FastAPI()
    register_exception_handlers(application)
    application.add_api_route("/boom/{kind}", raise_domain_error, methods=["GET"])
    return TestClient(application)


@pytest.mark.parametrize(
    ("kind", "expected_status", "expected_code"),
    [
        ("notfound", 404, "not_found"),
        ("denied", 403, "permission_denied"),
        ("conflict", 409, "conflict"),
    ],
)
def test_domain_errors_map_to_status_codes(
    failing_client, kind, expected_status, expected_code
):
    """Each domain error becomes its documented status code and error code."""
    response = failing_client.get(f"/boom/{kind}")
    assert response.status_code == expected_status
    assert response.json()["code"] == expected_code
    assert "detail" in response.json()
