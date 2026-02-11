from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Final

# Canonical contract events + compatibility events currently used in runtime.
ALLOWED_EVENT_TYPES: Final[set[str]] = {
    "connection_established",
    "diagnosis_started",
    "diagnosis_progress",
    "confirmation_required",
    "confirmation_rejected",
    "confirmation_status",
    "diagnosis_completed",
    "diagnosis_failed",
    "heartbeat",
    "replay_snapshot",
    "error",
    # Compatibility event aliases currently produced in services.
    "agent_message",
    "action_proposal",
    "diagnosis_status",
    "timeline_update",
    "confidence_update",
    "agent_trace_start",
    "agent_trace_step",
    "agent_trace_complete",
    "task_failed",
    "workflow_mode_degraded",
    "mode_router_decision",
    "workflow_node_entered",
    "workflow_node_completed",
    "confirmation_gate_decision",
    "action_approved",
    "action_rejected",
}


class InvalidDiagnosisEvent(ValueError):
    """Raised when a diagnosis event violates protocol contract."""


def validate_event_type(event_type: str) -> None:
    if event_type not in ALLOWED_EVENT_TYPES:
        raise InvalidDiagnosisEvent(f"Unknown diagnosis event type: {event_type}")


def normalize_event(event: Dict[str, Any]) -> Dict[str, Any]:
    event_type = event.get("type")
    if not isinstance(event_type, str):
        raise InvalidDiagnosisEvent("Diagnosis event must include string 'type'")

    validate_event_type(event_type)

    normalized = dict(event)
    normalized.setdefault("timestamp", datetime.now().isoformat())

    if "data" in normalized and not isinstance(normalized["data"], dict):
        raise InvalidDiagnosisEvent("Diagnosis event 'data' must be an object when present")

    return normalized
