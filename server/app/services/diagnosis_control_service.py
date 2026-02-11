from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.session_manager import session_manager
from app.services.state_manager import state_manager
from app.services.workflow_engine import workflow_engine
from app.tasks.diagnosis_tasks import run_diagnosis

logger = get_logger(__name__)

COMMAND_ACCEPTED = "command_accepted"
COMMAND_REJECTED = "command_rejected"
NO_PENDING_CONFIRMATION = "no_pending_confirmation"


@dataclass
class CommandResult:
    code: str
    session_id: str
    message: str
    details: Optional[Dict[str, Any]] = None


class DiagnosisControlService:
    def start_diagnosis(
        self,
        symptom: str,
        mode: str = "auto",
        context: Optional[Dict[str, Any]] = None,
        *,
        session_id: Optional[str] = None,
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        target_session_id = session_id or str(uuid.uuid4())
        session_manager.create_session(target_session_id, user_id)
        task = run_diagnosis.delay(target_session_id, symptom, mode, context)
        return {
            "status": "submitted",
            "session_id": target_session_id,
            "task_id": task.id,
            "message": "Diagnosis task submitted",
            "command_code": COMMAND_ACCEPTED,
        }

    def stop_diagnosis(self, session_id: str) -> CommandResult:
        if workflow_engine.cancel_workflow(session_id):
            session_manager.delete_session(session_id)
            return CommandResult(COMMAND_ACCEPTED, session_id, "Diagnosis stopped")
        return CommandResult(COMMAND_REJECTED, session_id, "Session not found")

    def pause_diagnosis(self, session_id: str) -> CommandResult:
        if workflow_engine.pause_workflow(session_id):
            return CommandResult(COMMAND_ACCEPTED, session_id, "Diagnosis paused")
        return CommandResult(COMMAND_REJECTED, session_id, "Session not found")

    def resume_diagnosis(self, session_id: str) -> CommandResult:
        if workflow_engine.resume_workflow(session_id):
            return CommandResult(COMMAND_ACCEPTED, session_id, "Diagnosis resumed")
        return CommandResult(COMMAND_REJECTED, session_id, "Session not found")

    def submit_confirmation_response(
        self,
        session_id: str,
        confirmation_id: str,
        response: Dict[str, Any],
        *,
        source: str,
    ) -> CommandResult:
        result = workflow_engine.submit_confirmation_response(session_id, confirmation_id, response)
        code = result.get("code", COMMAND_REJECTED)
        risk_level = result.get("risk_level")

        if code == COMMAND_ACCEPTED:
            self._record_confirmation_event(session_id, confirmation_id, response, source, risk_level)
            action = response.get("action", "approve")
            message = "Confirmation approved" if action == "approve" else "Confirmation rejected"
            return CommandResult(
                COMMAND_ACCEPTED,
                session_id,
                message,
                {
                    "confirmation_id": confirmation_id,
                    "action": action,
                    "risk_level": risk_level,
                },
            )

        if code == NO_PENDING_CONFIRMATION:
            return CommandResult(NO_PENDING_CONFIRMATION, session_id, f"No pending confirmation found: {confirmation_id}")

        return CommandResult(COMMAND_REJECTED, session_id, result.get("reason") or "Confirmation command rejected")

    def approve_action(self, session_id: str, action_id: str, *, source: str) -> CommandResult:
        return self.submit_confirmation_response(
            session_id,
            action_id,
            {
                "action": "approve",
                "actionId": action_id,
            },
            source=source,
        )

    def reject_action(self, session_id: str, action_id: str, reason: Optional[str], *, source: str) -> CommandResult:
        payload: Dict[str, Any] = {
            "action": "reject",
            "actionId": action_id,
        }
        if reason:
            payload["reason"] = reason
        return self.submit_confirmation_response(session_id, action_id, payload, source=source)

    def _record_confirmation_event(
        self,
        session_id: str,
        confirmation_id: str,
        response: Dict[str, Any],
        source: str,
        risk_level: Optional[str],
    ) -> None:
        db_gen = get_db()
        db = None
        try:
            db = next(db_gen)
            event_data: Dict[str, Any] = {
                "confirmation_id": confirmation_id,
                "response": response,
                "source": source,
            }
            if risk_level:
                event_data["risk_level"] = risk_level
            state_manager.record_event(session_id, "confirmation_response", event_data, db)
        except Exception as exc:
            logger.warning(f"Failed to persist confirmation response: {exc}")
        finally:
            if db is not None:
                db.close()
            db_gen.close()


diagnosis_control_service = DiagnosisControlService()
