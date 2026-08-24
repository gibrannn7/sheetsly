"""Tests for health endpoint and basic app configuration."""

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app_name"] == "Sheetsly"
    assert "engine" in data
    assert data["engine"]["python_analytical_engine"] == "active"
    assert data["engine"]["ai_integration"] == "disabled_for_phase_2"


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "Sheetsly"
    assert data["status"] == "online"
