import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_ok():
    """The health endpoint answers 200 with a status payload."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "documentation_path",
    ["/api/docs", "/api/redoc", "/api/openapi.json"],
)
def test_documentation_is_served_under_the_api_prefix(documentation_path):
    """Every documentation URL answers under /api, which is the only proxied prefix."""
    client = TestClient(app)
    assert client.get(documentation_path).status_code == 200


def test_docs_page_fetches_the_schema_from_the_api_prefix():
    """The Swagger page points at the prefixed schema, so it renders behind a proxy."""
    client = TestClient(app)
    response = client.get("/api/docs")
    assert "/api/openapi.json" in response.text
