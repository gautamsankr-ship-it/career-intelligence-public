from fastapi.testclient import TestClient

from app.api.dashboard import app


def test_dashboard_health_is_public_and_synthetic() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "demo": True}
