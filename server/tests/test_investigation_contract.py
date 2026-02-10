from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import investigation


app = FastAPI()
app.include_router(investigation.router, prefix="/investigation")
client = TestClient(app)


def test_stop_requires_session_id_in_body(monkeypatch):
    monkeypatch.setattr(
        "app.services.workflow_engine.workflow_engine.cancel_workflow",
        lambda _sid: True,
    )
    response = client.post("/investigation/stop", json={})
    assert response.status_code == 422


def test_stop_uses_body_payload(monkeypatch):
    called = {}

    def _cancel(session_id: str):
        called["session_id"] = session_id
        return True

    monkeypatch.setattr("app.services.workflow_engine.workflow_engine.cancel_workflow", _cancel)
    monkeypatch.setattr("app.api.v1.endpoints.investigation.session_manager.delete_session", lambda _sid: True)

    response = client.post("/investigation/stop", json={"session_id": "s-1"})

    assert response.status_code == 200
    assert response.json()["session_id"] == "s-1"
    assert called["session_id"] == "s-1"


def test_action_approve_requires_schema_fields():
    response = client.post("/investigation/action/approve", json={"session_id": "s-1"})
    assert response.status_code == 422


def test_action_reject_accepts_reason_optional():
    response = client.post(
        "/investigation/action/reject",
        json={"session_id": "s-1", "action_id": "a-1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == "s-1"
    assert payload["action_id"] == "a-1"
    assert payload["reason"] is None
