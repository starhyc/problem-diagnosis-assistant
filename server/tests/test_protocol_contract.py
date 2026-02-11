from app.contracts.diagnosis_protocol import InvalidDiagnosisEvent, normalize_event
from app.core.event_publisher import EventPublisher


class _FakeRedis:
    def __init__(self):
        self.messages = []

    def publish(self, channel, message):
        self.messages.append((channel, message))


def test_normalize_event_rejects_unknown_type():
    try:
        normalize_event({"type": "unexpected_event", "data": {}})
        raise AssertionError("Expected InvalidDiagnosisEvent")
    except InvalidDiagnosisEvent:
        pass


def test_event_publisher_rejects_unknown_type():
    publisher = EventPublisher()
    publisher.redis = _FakeRedis()

    ok = publisher.publish("diagnosis:s-1", {"type": "unexpected_event", "data": {}})

    assert ok is False
    assert publisher.redis.messages == []


def test_event_publisher_accepts_contract_event():
    publisher = EventPublisher()
    publisher.redis = _FakeRedis()

    ok = publisher.publish("diagnosis:s-1", {"type": "diagnosis_progress", "data": {"session_id": "s-1", "phase": "workflow"}})

    assert ok is True
    assert len(publisher.redis.messages) == 1


def test_confirmation_events_require_valid_risk_level():
    normalized = normalize_event({
        "type": "confirmation_required",
        "data": {"id": "c-1", "message": "need confirm", "riskLevel": "R2"},
    })
    assert normalized["type"] == "confirmation_required"

    for invalid in [
        {"type": "confirmation_required", "data": {"id": "c-2", "message": "missing"}},
        {"type": "confirmation_status", "data": {"confirmationId": "c-3", "status": "approved", "riskLevel": "high"}},
        {"type": "confirmation_rejected", "riskLevel": "critical", "data": {"reason": "rejected"}},
    ]:
        try:
            normalize_event(invalid)
            raise AssertionError("Expected InvalidDiagnosisEvent")
        except InvalidDiagnosisEvent:
            pass


def test_event_publisher_rejects_confirmation_event_with_invalid_risk_level():
    publisher = EventPublisher()
    publisher.redis = _FakeRedis()

    ok = publisher.publish(
        "diagnosis:s-1",
        {"type": "confirmation_status", "data": {"confirmationId": "cid", "status": "approved", "riskLevel": "medium"}},
    )

    assert ok is False
    assert publisher.redis.messages == []
