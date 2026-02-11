import asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints import websocket


app = FastAPI()
app.include_router(websocket.router)
client = TestClient(app)


class _FakeTask:
    id = "task-1"


class _FakeSubscriber:
    instances = []

    def __init__(self):
        self.stopped = 0
        _FakeSubscriber.instances.append(self)

    async def subscribe_to_diagnosis(self, session_id, callback):
        asyncio.create_task(
            callback(
                {
                    "type": "diagnosis_progress",
                    "data": {"session_id": session_id, "step": "started"},
                }
            )
        )

    def stop(self):
        self.stopped += 1


def _recv_until_types(ws, expected_types, max_messages=8):
    seen = []
    for _ in range(max_messages):
        message = ws.receive_json()
        seen.append(message)
        current_types = {item.get("type") for item in seen}
        if expected_types.issubset(current_types):
            return seen
    raise AssertionError(f"Did not receive expected types. Seen: {seen}")


def test_websocket_diagnosis_subscription_lifecycle(monkeypatch):
    websocket.manager.active_connections.clear()
    websocket.manager.subscribers.clear()
    _FakeSubscriber.instances.clear()

    monkeypatch.setattr(websocket, "EventSubscriber", _FakeSubscriber)
    monkeypatch.setattr("app.api.v1.endpoints.websocket.session_manager.create_session", lambda *_: True)
    monkeypatch.setattr("app.api.v1.endpoints.websocket.run_diagnosis.delay", lambda *_args, **_kwargs: _FakeTask())

    with client.websocket_connect("/agent/ws") as ws:
        connected = ws.receive_json()
        assert connected["type"] == "connection_established"
        session_id = connected["data"]["session_id"]

        ws.send_json({"type": "start_diagnosis", "data": {"symptom": "slow", "mode": "auto"}})

        received = _recv_until_types(ws, {"diagnosis_started", "diagnosis_progress"})
        assert any(msg.get("type") == "diagnosis_started" for msg in received)
        assert any(msg.get("type") == "diagnosis_progress" for msg in received)

        assert session_id in websocket.manager.subscribers

    assert session_id not in websocket.manager.subscribers
    assert _FakeSubscriber.instances
    assert _FakeSubscriber.instances[0].stopped == 1


def test_disconnect_is_idempotent_with_subscriber_stop(monkeypatch):
    websocket.manager.active_connections.clear()
    websocket.manager.subscribers.clear()

    subscriber = _FakeSubscriber()
    websocket.manager.subscribers["s-1"] = subscriber

    websocket.manager.disconnect("s-1")
    websocket.manager.disconnect("s-1")

    assert subscriber.stopped == 1
