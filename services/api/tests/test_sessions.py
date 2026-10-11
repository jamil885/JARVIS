import uuid

from fastapi.testclient import TestClient

from jarvis_api.main import create_app

client = TestClient(create_app())


def test_sessions_fail_closed_without_configured_token(monkeypatch):
    monkeypatch.delenv("JARVIS_API_TOKEN", raising=False)
    response = client.post("/api/v1/sessions", json={"title": "JARVIS"})
    assert response.status_code == 401


def test_sessions_reject_missing_and_wrong_bearer(monkeypatch):
    monkeypatch.setenv("JARVIS_API_TOKEN", "local-test-only-secret")
    assert client.post("/api/v1/sessions", json={"title": "JARVIS"}).status_code == 401
    response = client.post(
        "/api/v1/sessions",
        json={"title": "JARVIS"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


def test_sessions_require_database_after_authentication(monkeypatch):
    monkeypatch.setenv("JARVIS_API_TOKEN", "local-test-only-secret")
    monkeypatch.delenv("JARVIS_DATABASE_URL", raising=False)
    response = client.post(
        "/api/v1/sessions",
        json={"title": "JARVIS"},
        headers={"Authorization": "Bearer local-test-only-secret"},
    )
    assert response.status_code == 503


def test_invalid_uuid_path_rejected_without_db(monkeypatch):
    monkeypatch.setenv("JARVIS_API_TOKEN", "local-test-only-secret")
    response = client.get(
        "/api/v1/sessions/not-a-uuid",
        headers={"Authorization": "Bearer local-test-only-secret"},
    )
    assert response.status_code == 422


def test_session_routes_exposed_by_openapi():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/sessions" in paths
    assert "/api/v1/sessions/{session_id}" in paths
    assert "/api/v1/sessions/{session_id}/messages" in paths


def test_message_validation_requires_content_and_id(monkeypatch):
    monkeypatch.setenv("JARVIS_API_TOKEN", "local-test-only-secret")
    response = client.post(
        f"/api/v1/sessions/{uuid.uuid4()}/messages",
        json={"content": ""},
        headers={"Authorization": "Bearer local-test-only-secret"},
    )
    assert response.status_code == 422
