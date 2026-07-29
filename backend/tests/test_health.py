from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_reports_ok():
    """The health endpoint answers 200 with a status payload."""
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
