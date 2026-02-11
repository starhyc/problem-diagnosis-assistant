import uuid

from fastapi import APIRouter, HTTPException

from app.core.logging_config import get_logger
from app.core.session_manager import session_manager
from app.schemas.case import (
    ActionApprovalRequest,
    ActionRejectRequest,
    DiagnosisActionDecisionResponse,
    DiagnosisSessionControlResponse,
    StartDiagnosisRequest,
    StartDiagnosisResponse,
    StopDiagnosisRequest,
)
from app.tasks.diagnosis_tasks import run_diagnosis

logger = get_logger(__name__)
router = APIRouter()


@router.post("/start", response_model=StartDiagnosisResponse)
def start_diagnosis(request: StartDiagnosisRequest):
    session_id = str(uuid.uuid4())
    mode = request.mode if hasattr(request, "mode") else "auto"

    logger.info(f"Starting diagnosis: session_id={session_id}, problem={request.problem_description}")

    try:
        task = run_diagnosis.delay(session_id, request.problem_description, mode, request.context)
        return StartDiagnosisResponse(
            status="submitted",
            session_id=session_id,
            task_id=task.id,
            message="Diagnosis task submitted",
        )
    except Exception as exc:
        logger.error(f"Failed to start diagnosis: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to start diagnosis: {str(exc)}") from exc


@router.post("/stop", response_model=DiagnosisSessionControlResponse)
def stop_diagnosis(request: StopDiagnosisRequest):
    from app.services.workflow_engine import workflow_engine

    session_id = request.session_id
    success = workflow_engine.cancel_workflow(session_id)

    if success:
        session_manager.delete_session(session_id)
        return DiagnosisSessionControlResponse(
            status="stopped",
            session_id=session_id,
            message="Diagnosis stopped",
        )

    raise HTTPException(status_code=404, detail="Session not found")


@router.post("/action/approve", response_model=DiagnosisActionDecisionResponse)
def approve_action(request: ActionApprovalRequest):
    logger.info(f"Action approved: session_id={request.session_id}, action_id={request.action_id}")
    return DiagnosisActionDecisionResponse(
        status="approved",
        session_id=request.session_id,
        action_id=request.action_id,
        message="Action approved",
    )


@router.post("/action/reject", response_model=DiagnosisActionDecisionResponse)
def reject_action(request: ActionRejectRequest):
    logger.info(
        f"Action rejected: session_id={request.session_id}, action_id={request.action_id}, reason={request.reason}"
    )
    return DiagnosisActionDecisionResponse(
        status="rejected",
        session_id=request.session_id,
        action_id=request.action_id,
        reason=request.reason,
        message="Action rejected",
    )
