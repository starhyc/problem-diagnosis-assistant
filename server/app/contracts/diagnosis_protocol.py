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



CONFIRMATION_EVENT_TYPES: Final[set[str]] = {
    "confirmation_required",
    "confirmation_rejected",
    "confirmation_status",
    "confirmation_gate_decision",
}

ALLOWED_CONFIRMATION_RISK_LEVELS: Final[set[str]] = {"R0", "R1", "R2", "R3"}


def _extract_confirmation_risk_level(event_type: str, event: Dict[str, Any]) -> str | None:
    if event_type not in CONFIRMATION_EVENT_TYPES:
        return None

    direct = event.get("riskLevel") or event.get("risk_level")
    if isinstance(direct, str):
        return direct

    data = event.get("data")
    if isinstance(data, dict):
        nested = data.get("riskLevel") or data.get("risk_level")
        if isinstance(nested, str):
            return nested

    return None
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

    risk_level = _extract_confirmation_risk_level(event_type, normalized)
    if event_type in CONFIRMATION_EVENT_TYPES:
        if not risk_level:
            raise InvalidDiagnosisEvent(f"{event_type} must include riskLevel/risk_level")
        if risk_level not in ALLOWED_CONFIRMATION_RISK_LEVELS:
            raise InvalidDiagnosisEvent(
                f"{event_type} includes invalid risk level '{risk_level}', expected one of {sorted(ALLOWED_CONFIRMATION_RISK_LEVELS)}"
            )

    return normalized
