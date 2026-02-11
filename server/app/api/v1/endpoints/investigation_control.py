from fastapi import APIRouter, HTTPException

from app.core.logging_config import get_logger
from app.schemas.case import (
    ActionApprovalRequest,
    ActionRejectRequest,
    DiagnosisActionDecisionResponse,
    DiagnosisSessionControlResponse,
    StartDiagnosisRequest,
    StartDiagnosisResponse,
    StopDiagnosisRequest,
)
from app.services.diagnosis_control_service import diagnosis_control_service

logger = get_logger(__name__)
router = APIRouter()


@router.post("/start", response_model=StartDiagnosisResponse)
def start_diagnosis(request: StartDiagnosisRequest):
    mode = request.mode if hasattr(request, "mode") else "auto"
    logger.info(f"Starting diagnosis: problem={request.problem_description}")

    try:
        result = diagnosis_control_service.start_diagnosis(
            request.problem_description,
            mode,
            request.context,
        )
        return StartDiagnosisResponse(
            status=result["status"],
            session_id=result["session_id"],
            task_id=result["task_id"],
            message=result["message"],
            command_code=result["command_code"],
        )
    except Exception as exc:
        logger.error(f"Failed to start diagnosis: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to start diagnosis: {str(exc)}") from exc


@router.post("/stop", response_model=DiagnosisSessionControlResponse)
def stop_diagnosis(request: StopDiagnosisRequest):
    result = diagnosis_control_service.stop_diagnosis(request.session_id)
    status = "stopped" if result.code == "command_accepted" else "unchanged"
    return DiagnosisSessionControlResponse(
        status=status,
        session_id=request.session_id,
        message=result.message,
        command_code=result.code,
    )


@router.post("/action/approve", response_model=DiagnosisActionDecisionResponse)
def approve_action(request: ActionApprovalRequest):
    result = diagnosis_control_service.approve_action(request.session_id, request.action_id, source="rest")
    status = "approved" if result.code == "command_accepted" else "pending"
    return DiagnosisActionDecisionResponse(
        status=status,
        session_id=request.session_id,
        action_id=request.action_id,
        message=result.message,
        command_code=result.code,
    )


@router.post("/action/reject", response_model=DiagnosisActionDecisionResponse)
def reject_action(request: ActionRejectRequest):
    result = diagnosis_control_service.reject_action(
        request.session_id,
        request.action_id,
        request.reason,
        source="rest",
    )
    status = "rejected" if result.code == "command_accepted" else "pending"
    return DiagnosisActionDecisionResponse(
        status=status,
        session_id=request.session_id,
        action_id=request.action_id,
        reason=request.reason,
        message=result.message,
        command_code=result.code,
    )
