from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.case import HistoryDetailResponse, HistoryEventResponse, HistoryListItemResponse
from app.services.state_manager import state_manager
from app.services.settings_audit import SettingsAuditService

router = APIRouter()
audit_service = SettingsAuditService()


@router.get("", response_model=List[HistoryListItemResponse])
def list_history_sessions(
    start_time: Optional[str] = Query(default=None),
    end_time: Optional[str] = Query(default=None),
    service: Optional[str] = Query(default=None),
    problem_type: Optional[str] = Query(default=None),
    sort_by: str = Query(default="updated_at"),
    sort_order: str = Query(default="desc"),
    db: Session = Depends(get_db),
):
    return state_manager.list_sessions(
        db=db,
        start_time=start_time,
        end_time=end_time,
        service=service,
        problem_type=problem_type,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get("/{session_id}", response_model=HistoryDetailResponse)
def get_history_detail(session_id: str, db: Session = Depends(get_db)):
    detail = state_manager.get_session_detail(session_id, db)
    if not detail:
        raise HTTPException(status_code=404, detail="History session not found")
    return detail


@router.get("/{session_id}/events", response_model=List[HistoryEventResponse])
def replay_history_events(session_id: str, db: Session = Depends(get_db)):
    detail = state_manager.get_session_detail(session_id, db)
    if not detail:
        raise HTTPException(status_code=404, detail="History session not found")
    return state_manager.get_session_events(session_id, db)


@router.get("/{session_id}/settings-audit", response_model=List[dict])
def get_session_settings_audit(
    session_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    detail = state_manager.get_session_detail(session_id, db)
    if not detail:
        raise HTTPException(status_code=404, detail="History session not found")
    return audit_service.list_by_session_id(session_id=session_id, limit=limit)
