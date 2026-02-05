from celery import Task
from app.core.celery_app import celery_app
from app.core.logging_config import get_logger
from app.core.database import get_db
from app.services.workflow_engine import workflow_engine, DiagnosisState
from app.services.state_manager import state_manager
from app.core.event_publisher import event_publisher
from typing import Dict, Any
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

@celery_app.task(bind=True, base=DiagnosisTask, max_retries=3)
def run_diagnosis(self, session_id: str, symptom: str, mode: str = "simple") -> Dict[str, Any]:
    """Run diagnosis workflow as Celery task"""
    logger.info(f"Starting diagnosis task for session: {session_id}")

    try:
        # Update task progress
        self.update_state(state='PROGRESS', meta={'progress': 0, 'phase': 'initializing'})

        # Publish start event
        event_publisher.publish_diagnosis_event(session_id, {
            "type": "diagnosis_started",
            "session_id": session_id,
            "symptom": symptom,
            "task_id": self.request.id
        })

        # Initialize state
        state = state_manager.create_state(session_id)
        self.update_state(state='PROGRESS', meta={'progress': 20, 'phase': 'workflow_execution'})

        # Create initial workflow state
        workflow_state: DiagnosisState = {
            "symptom": symptom,
            "messages": [],
            "hypothesis_tree": {},
            "evidence": [],
            "confidence": 0,
            "next_action": None,
            "current_phase": "init",
            "paused": False,
            "cancelled": False
        }

        # Run workflow
        if mode == "simple":
            workflow = workflow_engine.create_simple_workflow()
            self.update_state(state='PROGRESS', meta={'progress': 50, 'phase': 'simple_workflow'})
            result = asyncio.run(workflow(workflow_state))
        else:
            workflow = workflow_engine.create_complex_workflow()
            self.update_state(state='PROGRESS', meta={'progress': 50, 'phase': 'complex_workflow'})
            result = asyncio.run(workflow.ainvoke(workflow_state))

        self.update_state(state='PROGRESS', meta={'progress': 80, 'phase': 'saving_results'})

        # Save final state
        db = next(get_db())
        state_manager.update_state(session_id, result)
        state_manager.save_snapshot(session_id, db)
        state_manager.record_event(session_id, "diagnosis_completed", {"result": result}, db)

        # Persist task result
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

        # Publish completion event
        event_publisher.publish_diagnosis_event(session_id, {
            "type": "diagnosis_completed",
            "session_id": session_id,
            "confidence": result.get("confidence", 0)
        })

        logger.info(f"Diagnosis task completed for session: {session_id}")
        return {"status": "completed", "session_id": session_id, "result": result}

    except Exception as e:
        logger.error(f"Diagnosis task error for session {session_id}: {e}")
        raise self.retry(exc=e, countdown=2 ** self.request.retries)
