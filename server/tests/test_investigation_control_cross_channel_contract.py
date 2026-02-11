from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import investigation_control, websocket


app = FastAPI()
app.include_router(investigation_control.router, prefix="/investigation")
app.include_router(websocket.router)
client = TestClient(app)


def _recv_until(ws, expected_type: str, max_messages: int = 6):
    for _ in range(max_messages):
        message = ws.receive_json()
        if message.get("type") == expected_type:
            return message
    raise AssertionError(f"Did not receive expected message: {expected_type}")


def test_rest_and_websocket_share_confirmation_command_contract(monkeypatch):
    websocket.manager.active_connections.clear()
    websocket.manager.subscribers.clear()

    async def _noop_subscribe(_sid):
        return None

    monkeypatch.setattr(websocket.manager, "subscribe_to_events", _noop_subscribe)
    monkeypatch.setattr(
        "app.api.v1.endpoints.websocket.diagnosis_control_service.start_diagnosis",
        lambda *_args, **_kwargs: {
            "status": "submitted",
            "task_id": "task-contract-1",
            "command_code": "command_accepted",
        },
    )

    seen_confirmations = set()
    persisted = []

    def _fake_submit(session_id: str, confirmation_id: str, _response: dict):
        key = (session_id, confirmation_id)
        if key in seen_confirmations:
            return {"code": "no_pending_confirmation"}
        seen_confirmations.add(key)
        return {"code": "command_accepted", "risk_level": "R1"}

    monkeypatch.setattr(
        "app.services.diagnosis_control_service.workflow_engine.submit_confirmation_response",
        _fake_submit,
    )
    monkeypatch.setattr(
        "app.services.diagnosis_control_service.DiagnosisControlService._record_confirmation_event",
        lambda self, session_id, confirmation_id, response, source, risk_level: persisted.append(
            {
                "session_id": session_id,
                "confirmation_id": confirmation_id,
                "response": response,
                "source": source,
                "risk_level": risk_level,
            }
        ),
    )

    with client.websocket_connect("/agent/ws") as ws:
        connected = ws.receive_json()
        session_id = connected["data"]["session_id"]

        ws.send_json({"type": "start_diagnosis", "data": {"symptom": "cpu", "mode": "auto"}})
        started = _recv_until(ws, "diagnosis_started")
        assert started["data"]["command_code"] == "command_accepted"

        approve_resp = client.post(
            "/investigation/action/approve",
            json={"session_id": session_id, "action_id": "confirm-1"},
        )
        assert approve_resp.status_code == 200
        assert approve_resp.json()["command_code"] == "command_accepted"

        ws.send_json(
            {
                "type": "confirmation_response",
                "data": {
                    "confirmationId": "confirm-1",
                    "response": {"action": "approve", "actionId": "confirm-1"},
                },
            }
        )
        confirmation_status = _recv_until(ws, "confirmation_status")
        assert confirmation_status["data"]["command_code"] == "no_pending_confirmation"

    assert persisted == [
        {
            "session_id": session_id,
            "confirmation_id": "confirm-1",
            "response": {"action": "approve", "actionId": "confirm-1"},
            "source": "rest",
            "risk_level": "R1",
        }
    ]
