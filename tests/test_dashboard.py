from fastapi.testclient import TestClient

from app.api.dashboard import app


def test_dashboard_exposes_synthetic_action_required_page() -> None:
    response = TestClient(app).get("/action-required")
    assert response.status_code == 200
    assert "synthetic answer group" in response.text
