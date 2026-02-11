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
