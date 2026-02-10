from celery import Task
from app.core.celery_app import celery_app
from app.core.logging_config import get_logger
from app.core.database import get_db
from app.services.workflow_engine import workflow_engine, DiagnosisState
from app.services.state_manager import state_manager
from app.core.event_publisher import event_publisher
from app.services.mode_router import mode_router, DiagnosisMode, TaskFeatures, normalize_mode
from typing import Dict, Any, Optional
import asyncio

logger = get_logger(__name__)


class DiagnosisTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        session_id = kwargs.get("session_id")
        if session_id:
            event_publisher.publish_diagnosis_event(session_id, {
                "type": "task_failed",
                "task_id": task_id,
                "error": str(exc)
            })


def _normalize_mode(mode: Optional[str]) -> str:
    if not mode:
        return "auto"

    mode_alias = {
        "simple": DiagnosisMode.DIRECT.value,
        "complex": DiagnosisMode.REACT.value,
        "auto": "auto",
    }
    normalized = normalize_mode(mode)
    if not normalized:
        return "auto"
    return mode_alias.get(normalized, normalized)


@celery_app.task(bind=True, base=DiagnosisTask, max_retries=3)
def run_diagnosis(self, session_id: str, symptom: str, mode: str = "auto", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Run diagnosis workflow as Celery task"""
    logger.info(f"Starting diagnosis task for session: {session_id}")

    try:
        self.update_state(state='PROGRESS', meta={'progress': 0, 'phase': 'initializing'})

        normalized_mode = _normalize_mode(mode)
        context = context or {}
        decision_trace = []

        explicit_mode = normalized_mode if normalized_mode != "auto" else None

        if explicit_mode:
            selected_mode = explicit_mode
            decision_trace.append({"stage": "explicit_specified", "mode": selected_mode})
        else:
            features = TaskFeatures(
                step_complexity=context.get("step_complexity", 4),
                cross_domain_count=context.get("cross_domain_count", 1),
                uncertainty=context.get("uncertainty", 3),
            )
            recommendation = mode_router.recommend_mode(features)
            recommended_mode = recommendation.get("mode")
            if recommended_mode:
                selected_mode = recommended_mode
                decision_trace.append({"stage": "router_recommend", **recommendation})
            else:
                selected_mode = DiagnosisMode.PLAN_EXECUTE.value
                decision_trace.append({"stage": "default", "mode": selected_mode})

        event_publisher.publish_diagnosis_event(session_id, {
            "type": "diagnosis_started",
            "session_id": session_id,
            "symptom": symptom,
            "task_id": self.request.id,
            "mode": selected_mode,
            "mode_decision": decision_trace,
        })

        state_manager.create_state(session_id)
        self.update_state(state='PROGRESS', meta={'progress': 20, 'phase': 'workflow_execution'})

        workflow_state: DiagnosisState = {
            "session_id": session_id,
            "symptom": symptom,
            "messages": [],
            "hypothesis_tree": {},
            "evidence": [],
            "confidence": 0,
            "next_action": None,
            "current_phase": "init",
            "paused": False,
            "cancelled": False,
            "pending_confirmations": [],
            "audit_logs": [],
            "mode": selected_mode,
            "mode_history": decision_trace.copy(),
        }

        self.update_state(state='PROGRESS', meta={'progress': 50, 'phase': f'{selected_mode}_workflow'})
        result = asyncio.run(workflow_engine.run(selected_mode, workflow_state))

        self.update_state(state='PROGRESS', meta={'progress': 80, 'phase': 'saving_results'})

        db = next(get_db())
        state_manager.update_state(session_id, result)
        state_manager.save_snapshot(session_id, db)
        state_manager.record_event(session_id, "diagnosis_completed", {"result": result, "mode_decision": decision_trace}, db)

        from sqlalchemy import text
        db.execute(
            text("""
                INSERT INTO agent_executions (session_id, agent_type, task_id, status, result_data)
                VALUES (:session_id, :agent_type, :task_id, :status, :result_data)
            """),
            {
                "session_id": session_id,
                "agent_type": "workflow",
                "task_id": self.request.id,
                "status": "completed",
                "result_data": str(result)
            }
        )
        db.commit()

        event_publisher.publish_diagnosis_event(session_id, {
            "type": "diagnosis_completed",
            "session_id": session_id,
            "confidence": result.get("confidence", 0),
            "mode": result.get("mode", selected_mode),
            "mode_decision": result.get("mode_history", decision_trace),
        })

        logger.info(f"Diagnosis task completed for session: {session_id}")
        return {
            "status": "completed",
            "session_id": session_id,
            "mode": result.get("mode", selected_mode),
            "mode_decision": result.get("mode_history", decision_trace),
            "result": result,
        }

    except Exception as e:
        logger.error(f"Diagnosis task error for session {session_id}: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
