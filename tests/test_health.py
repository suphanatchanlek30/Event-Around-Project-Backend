# tests/test_health.py

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Event Around API is running"
    assert body["data"]["service"] == "Event Around API"
    assert body["data"]["apiPrefix"] == "/api/v1"
    assert "serverTime" in body["data"]


def test_root_endpoint_has_service_metadata():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["service"] == "Event Around API"
    assert body["data"]["apiPrefix"] == "/api/v1"